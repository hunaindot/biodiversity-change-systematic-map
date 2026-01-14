from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence
from uuid import uuid4
import zlib

from openai import OpenAI

from .config import DEFAULT_MODEL, DEFAULT_REASONING_EFFORT, MAPPINGS_DIR
from .openai_batches import build_client, format_article
from .openai_live import run_live_requests, serialize_live_body


def _coerce_text_param(structured_output: Any) -> dict | None:
    if structured_output is None:
        return None
    text_format = structured_output
    if isinstance(structured_output, dict):
        text_format = structured_output.get("text") or structured_output.get("format") or structured_output
    if not text_format:
        return None
    if isinstance(text_format, dict) and "format" in text_format:
        return text_format
    return {"format": text_format}


def _normalize_request_dest(dest: Path) -> Path:
    if dest.parent.name.lower() == "data":
        return dest.parent.parent / "request" / dest.name
    return dest


def _custom_id(doc: dict | None) -> str:
    if not doc:
        return ""
    cid = doc.get("UT") or doc.get("id") or ""
    return str(cid)


def _get_prompt_config(prompts: dict | None, key: str) -> dict:
    if not prompts or key not in prompts:
        raise KeyError(f"Prompt config '{key}' not found in loaded prompts.")
    config = prompts[key]
    if not isinstance(config, dict):
        raise ValueError(f"Prompt config '{key}' must be a mapping.")
    return config


def _build_standard_request(
    doc: dict,
    prompt_config: dict,
    model: str = DEFAULT_MODEL,
    reasoning_effort: str | None = DEFAULT_REASONING_EFFORT,
) -> dict:
    system_prompt = prompt_config["system_prompt"]
    text_param = _coerce_text_param(prompt_config.get("structured_output"))
    prompt = format_article(doc)
    body: dict[str, Any] = {
        "model": model,
        "input": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    }
    if reasoning_effort:
        body["reasoning"] = {"effort": reasoning_effort}
    if text_param:
        body["text"] = text_param
    return {
        "custom_id": _custom_id(doc),
        "method": "POST",
        "url": "/v1/responses",
        "body": body,
    }


def _write_request_lines(documents: Sequence[dict], dest: Path, builder) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as f:
        for doc in documents:
            f.write(json.dumps(builder(doc), ensure_ascii=False) + "\n")
    return dest


def _load_processed_custom_ids(out_path: Path) -> set[str]:
    processed: set[str] = set()
    if not out_path.exists():
        return processed
    for line in out_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        cid = record.get("custom_id")
        if cid:
            processed.add(str(cid))
    return processed


def _extract_output_text(resp: Any, body: Any) -> str | None:
    text = getattr(resp, "output_text", None)
    if text:
        return str(text)
    if isinstance(body, str):
        return body
    if isinstance(body, dict):
        if "output_text" in body:
            return body["output_text"]
        output = body.get("output") or body.get("outputs")
        if isinstance(output, list) and output:
            candidate = output[0]
            if isinstance(candidate, dict):
                content = candidate.get("content") or []
                if isinstance(content, list) and content:
                    text_block = content[0].get("text")
                    if isinstance(text_block, dict):
                        return text_block.get("value") or text_block.get("content")
    return None


def _parse_output_payload(resp: Any, body: Any) -> tuple[dict | None, str | None]:
    output_text = _extract_output_text(resp, body)
    if not output_text:
        return None, "Missing output_text on response."
    try:
        return json.loads(str(output_text).strip()), None
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON in response: {exc}"


@dataclass
class TaskDefinition:
    name: str
    prompt_key: str
    supports_batch: bool = True
    supports_live: bool = True
    output_prefix: str | None = None

    def build_requests_file(
        self,
        documents: Sequence[dict],
        dest: Path,
        prompts: dict,
        model: str = DEFAULT_MODEL,
        reasoning_effort: str = DEFAULT_REASONING_EFFORT,
    ) -> Path:
        raise NotImplementedError

    def run_live(
        self,
        request_paths: Iterable[Path | str],
        output_dir: Path,
        client: OpenAI | None = None,
        default_model: str = DEFAULT_MODEL,
        default_reasoning: str = DEFAULT_REASONING_EFFORT,
        prompts: dict | None = None,
        skip_existing: bool = True,
    ) -> list[dict]:
        raise NotImplementedError

    def batch_metadata(self, run_name: str) -> dict:
        return {"run": run_name, "type": self.name}


@dataclass
class SimpleTask(TaskDefinition):
    def build_requests_file(
        self,
        documents: Sequence[dict],
        dest: Path,
        prompts: dict,
        model: str = DEFAULT_MODEL,
        reasoning_effort: str = DEFAULT_REASONING_EFFORT,
    ) -> Path:
        prompt_config = _get_prompt_config(prompts, self.prompt_key)
        dest = _normalize_request_dest(Path(dest))
        return _write_request_lines(
            documents,
            dest,
            lambda doc: _build_standard_request(doc, prompt_config, model=model, reasoning_effort=reasoning_effort),
        )

    def run_live(
        self,
        request_paths: Iterable[Path | str],
        output_dir: Path,
        client: OpenAI | None = None,
        default_model: str = DEFAULT_MODEL,
        default_reasoning: str = DEFAULT_REASONING_EFFORT,
        prompts: dict | None = None,
        skip_existing: bool = True,
    ) -> list[dict]:
        client = client or build_client()
        prefix = self.output_prefix or self.name
        return run_live_requests(
            request_paths,
            output_dir=output_dir,
            client=client,
            default_model=default_model,
            default_reasoning=default_reasoning,
            output_prefix=prefix,
            skip_existing=skip_existing,
        )


@dataclass
class EcosystemTask(TaskDefinition):
    mapping_filename: str = "ecosystem_typology_1_3_with_short_desc.json"

    def build_requests_file(
        self,
        documents: Sequence[dict],
        dest: Path,
        prompts: dict,
        model: str = DEFAULT_MODEL,
        reasoning_effort: str = DEFAULT_REASONING_EFFORT,
    ) -> Path:
        _get_prompt_config(prompts, self.prompt_key)  # validate presence
        dest = _normalize_request_dest(Path(dest))
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("w", encoding="utf-8") as f:
            for doc in documents:
                record = {
                    "custom_id": _custom_id(doc),
                    "article_text": format_article(doc),
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return dest

    def run_live(
        self,
        request_paths: Iterable[Path | str],
        output_dir: Path,
        client: OpenAI | None = None,
        default_model: str = DEFAULT_MODEL,
        default_reasoning: str = DEFAULT_REASONING_EFFORT,
        prompts: dict | None = None,
        skip_existing: bool = True,
    ) -> list[dict]:
        prompt_config = _get_prompt_config(prompts, self.prompt_key)
        text_param = _coerce_text_param(prompt_config.get("structured_output"))
        system_prompt = prompt_config["system_prompt"]
        mapping = self._load_mapping()

        client = client or build_client()
        output_dir.mkdir(parents=True, exist_ok=True)

        entries: list[dict] = []
        for req_path in request_paths:
            req_path = Path(req_path)
            out_path = output_dir / f"{(self.output_prefix or self.name)}-{req_path.stem}.jsonl"
            processed_ids = _load_processed_custom_ids(out_path) if skip_existing else set()
            skipped_count = 0
            rendered_count = 0
            mode = "a" if out_path.exists() else "w"

            with req_path.open("r", encoding="utf-8") as src, out_path.open(mode, encoding="utf-8") as dest:
                for line in src:
                    if not line.strip():
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError as exc:
                        record = {
                            "id": f"{self.name}_live_{uuid4().hex}",
                            "custom_id": None,
                            "responses": {},
                            "results_payload": {},
                            "error": {"message": f"Invalid request JSON: {exc}"},
                        }
                        dest.write(json.dumps(record, ensure_ascii=False) + "\n")
                        rendered_count += 1
                        continue

                    custom_id = payload.get("custom_id") or payload.get("id")
                    if custom_id:
                        custom_id = str(custom_id)
                    if skip_existing and custom_id and custom_id in processed_ids:
                        print(f"Skipping already processed custom_id {custom_id} from {req_path}")
                        skipped_count += 1
                        continue

                    article_text = payload.get("article_text") or payload.get("prompt") or ""
                    record = self._run_ecosystem_workflow(
                        article_text=article_text,
                        client=client,
                        system_prompt=system_prompt,
                        text_param=text_param,
                        mapping=mapping,
                        model=default_model,
                        reasoning=default_reasoning,
                        custom_id=custom_id or "",
                    )
                    dest.write(json.dumps(record, ensure_ascii=False) + "\n")
                    rendered_count += 1

            entries.append(
                {
                    "mode": "live",
                    "request_path": str(req_path),
                    "output_path": str(out_path),
                    "status": "completed",
                    "responses": rendered_count,
                    "skipped": skipped_count,
                }
            )
            print(f"Wrote {rendered_count} ecosystem outputs to {out_path} (skipped {skipped_count})")

        return entries

    def _load_mapping(self) -> dict:
        path = MAPPINGS_DIR / self.mapping_filename
        if not path.exists():
            raise FileNotFoundError(f"Ecosystem mapping file not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _call_stage(
        self,
        *,
        stage_label: str,
        prompt_input: str,
        client: OpenAI,
        system_prompt: str,
        text_param: dict | None,
        model: str,
        reasoning: str | None,
        previous_response_id: str | None = None,
        prompt_cache_key: str | None = None,  
    ) -> dict:
        kwargs: dict[str, Any] = {"model": model, "instructions": system_prompt, "input": prompt_input}

        # if prompt_cache_key:
        #     kwargs["prompt_cache_key"] = prompt_cache_key 
        if previous_response_id:
            kwargs["previous_response_id"] = previous_response_id
        if text_param:
            kwargs["text"] = text_param
        if reasoning:
            kwargs["reasoning"] = {"effort": reasoning}

        try:
            resp = client.responses.create(**kwargs)
        except Exception as exc:
            return {
                "status_code": None,
                "request_id": None,
                "body": None,
                "payload": None,
                "error": f"{stage_label} request failed: {exc}",
            }

        body = serialize_live_body(resp)
        payload, parse_error = _parse_output_payload(resp, body)
        request_id = getattr(resp, "id", None)
        if isinstance(body, dict) and not request_id:
            request_id = body.get("id")
        return {
            "status_code": 200,
            "request_id": request_id,
            "body": body,
            "payload": payload,
            "error": parse_error,
        }

    @staticmethod
    def _extract_labels(payload: dict | None) -> list[str]:
        if not payload:
            return []
        results = payload.get("results")
        if isinstance(results, list):
            return [str(item) for item in results if item is not None]
        return []

    @staticmethod
    def _should_continue(payload: dict | None) -> bool:
        if not payload:
            return False
        return payload.get("stop_reason") == "continue"

    def _build_biome_candidates(self, realm_labels: list[str], mapping: dict) -> tuple[list[dict], dict[str, list]]:
        candidates: list[dict] = []
        lookup: dict[str, list] = {}
        seen: set[str] = set()
        for label in realm_labels:
            realm_info = mapping.get(label, {})
            for biome in realm_info.get("biomes", []):
                name = biome.get("name")
                if not name or name in seen:
                    continue
                candidates.append({"name": name, "desc": biome.get("short_desc", "")})
                lookup[name] = biome.get("efg", [])
                seen.add(name)
        return candidates, lookup

    def _build_efg_candidates(self, biome_labels: list[str], biome_lookup: dict[str, list]) -> list[dict]:
        candidates: list[dict] = []
        seen: set[str] = set()
        for biome_name in biome_labels:
            for efg in biome_lookup.get(biome_name, []):
                name = efg.get("name")
                if not name or name in seen:
                    continue
                candidates.append({"name": name, "desc": efg.get("short_desc", "")})
                seen.add(name)
        return candidates

    def _run_ecosystem_workflow(
        self,
        *,
        article_text: str,
        client: OpenAI,
        system_prompt: str,
        text_param: dict | None,
        mapping: dict,
        model: str,
        reasoning: str | None,
        custom_id: str,
        max_iterations: int = 5,
    ) -> dict:
        article_text = article_text or ""
        responses: dict[str, Any] = {"realm": None, "biome": None, "efg": None}
        results_payload: dict[str, Any] = {"realms": None, "biomes": None, "efgs": None}
        workflow_error: str | None = None
        iteration = 0
        workflow_active = True
        realm_labels: list[str] = []
        biome_labels: list[str] = []
        efg_labels: list[str] = []
        previous_response_id: str | None = None
        biome_lookup: dict[str, list] = {}
        shard = custom_id
        cache_key = f"ecosys_v1:shard_{shard}"

        while workflow_active and iteration < max_iterations:
            iteration += 1

            if not realm_labels:
                prompt_input = f"ARTICLE_TEXT:\\n{article_text}"
                stage = self._call_stage(
                    stage_label="realm",
                    prompt_input=prompt_input,
                    client=client,
                    system_prompt=system_prompt,
                    text_param=text_param,
                    model=model,
                    reasoning=reasoning,
                    previous_response_id=None,
                    prompt_cache_key=cache_key
                )
                responses["realm"] = stage
                results_payload["realms"] = stage.get("payload")
                previous_response_id = stage.get("request_id") or previous_response_id
                if stage.get("error"):
                    workflow_error = stage["error"]
                    workflow_active = False
                    break
                realm_labels = self._extract_labels(stage.get("payload"))
                workflow_active = bool(realm_labels) and self._should_continue(stage.get("payload"))
                if not workflow_active:
                    break

            if not biome_labels and workflow_active:
                biome_candidates, biome_lookup = self._build_biome_candidates(realm_labels, mapping)
                if not biome_candidates:
                    biome_data = {"results": ["No biome candidates found"], "stop_reason": "stop-manual"}
                    responses["biome"] = {
                        "status_code": None,
                        "request_id": None,
                        "body": None,
                        "payload": biome_data,
                        "error": None,
                    }
                    results_payload["biomes"] = biome_data
                    workflow_active = False
                    break

                prompt_input = (
                    f"BIOME_CANDIDATES:\\n{json.dumps(biome_candidates, indent=2)}"
                )
                stage = self._call_stage(
                    stage_label="biome",
                    prompt_input=prompt_input,
                    client=client,
                    system_prompt=system_prompt,
                    text_param=text_param,
                    model=model,
                    reasoning=reasoning,
                    previous_response_id=previous_response_id,
                    prompt_cache_key=cache_key
                )
                responses["biome"] = stage
                results_payload["biomes"] = stage.get("payload")
                previous_response_id = stage.get("request_id") or previous_response_id
                if stage.get("error"):
                    workflow_error = stage["error"]
                    workflow_active = False
                    break
                biome_labels = self._extract_labels(stage.get("payload"))
                workflow_active = bool(biome_labels) and self._should_continue(stage.get("payload"))
                if not workflow_active:
                    break

            if not efg_labels and workflow_active:
                efg_candidates = self._build_efg_candidates(biome_labels, biome_lookup)
                if not efg_candidates:
                    efg_data = {"results": ["No EFG candidates found"], "stop_reason": "stop-manual"}
                    responses["efg"] = {
                        "status_code": None,
                        "request_id": None,
                        "body": None,
                        "payload": efg_data,
                        "error": None,
                    }
                    results_payload["efgs"] = efg_data
                    workflow_active = False
                    break

                prompt_input = (
                    f"EFG_CANDIDATES:\\n{json.dumps(efg_candidates, indent=2)}"
                )
                stage = self._call_stage(
                    stage_label="efg",
                    prompt_input=prompt_input,
                    client=client,
                    system_prompt=system_prompt,
                    text_param=text_param,
                    model=model,
                    reasoning=reasoning,
                    previous_response_id=previous_response_id,
                    prompt_cache_key=cache_key
                )
                responses["efg"] = stage
                results_payload["efgs"] = stage.get("payload")
                previous_response_id = stage.get("request_id") or previous_response_id
                if stage.get("error"):
                    workflow_error = stage["error"]
                efg_labels = self._extract_labels(stage.get("payload"))
                workflow_active = False

            if realm_labels and biome_labels and efg_labels:
                break

        if workflow_active and iteration >= max_iterations:
            workflow_error = f"Max iterations reached ({max_iterations})."

        return {
            "id": f"{self.name}_live_{uuid4().hex}",
            "custom_id": custom_id,
            "responses": responses,
            "results_payload": results_payload,
            "error": {"message": workflow_error} if workflow_error else None,
            "iterations": iteration,
        }


@dataclass
class ThreatTask(TaskDefinition):
    mapping_filename: str = "threats_classification.json"

    def build_requests_file(
        self,
        documents: Sequence[dict],
        dest: Path,
        prompts: dict,
        model: str = DEFAULT_MODEL,
        reasoning_effort: str = DEFAULT_REASONING_EFFORT,
    ) -> Path:
        _get_prompt_config(prompts, self.prompt_key)  # validate presence
        dest = _normalize_request_dest(Path(dest))
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("w", encoding="utf-8") as f:
            for doc in documents:
                record = {
                    "custom_id": _custom_id(doc),
                    "article_text": format_article(doc),
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return dest

    def run_live(
        self,
        request_paths: Iterable[Path | str],
        output_dir: Path,
        client: OpenAI | None = None,
        default_model: str = DEFAULT_MODEL,
        default_reasoning: str = DEFAULT_REASONING_EFFORT,
        prompts: dict | None = None,
        skip_existing: bool = True,
    ) -> list[dict]:
        prompt_config = _get_prompt_config(prompts, self.prompt_key)
        text_param = _coerce_text_param(prompt_config.get("structured_output"))
        system_prompt = prompt_config["system_prompt"]
        mapping = self._load_mapping()

        client = client or build_client()
        output_dir.mkdir(parents=True, exist_ok=True)

        entries: list[dict] = []
        for req_path in request_paths:
            req_path = Path(req_path)
            out_path = output_dir / f"{(self.output_prefix or self.name)}-{req_path.stem}.jsonl"
            processed_ids = _load_processed_custom_ids(out_path) if skip_existing else set()
            skipped_count = 0
            rendered_count = 0
            mode = "a" if out_path.exists() else "w"

            with req_path.open("r", encoding="utf-8") as src, out_path.open(mode, encoding="utf-8") as dest:
                for line in src:
                    if not line.strip():
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError as exc:
                        record = {
                            "id": f"{self.name}_live_{uuid4().hex}",
                            "custom_id": None,
                            "responses": {},
                            "results_payload": {},
                            "error": {"message": f"Invalid request JSON: {exc}"},
                        }
                        dest.write(json.dumps(record, ensure_ascii=False) + "\n")
                        rendered_count += 1
                        continue

                    custom_id = payload.get("custom_id") or payload.get("id")
                    if custom_id:
                        custom_id = str(custom_id)
                    if skip_existing and custom_id and custom_id in processed_ids:
                        print(f"Skipping already processed custom_id {custom_id} from {req_path}")
                        skipped_count += 1
                        continue

                    article_text = payload.get("article_text") or payload.get("prompt") or ""
                    record = self._run_threat_workflow(
                        article_text=article_text,
                        client=client,
                        system_prompt=system_prompt,
                        text_param=text_param,
                        mapping=mapping,
                        model=default_model,
                        reasoning=default_reasoning,
                        custom_id=custom_id or "",
                    )
                    dest.write(json.dumps(record, ensure_ascii=False) + "\n")
                    rendered_count += 1

            entries.append(
                {
                    "mode": "live",
                    "request_path": str(req_path),
                    "output_path": str(out_path),
                    "status": "completed",
                    "responses": rendered_count,
                    "skipped": skipped_count,
                }
            )
            print(f"Wrote {rendered_count} threats outputs to {out_path} (skipped {skipped_count})")

        return entries

    def _load_mapping(self) -> dict:
        path = MAPPINGS_DIR / self.mapping_filename
        if not path.exists():
            raise FileNotFoundError(f"Threat mapping file not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _call_stage(
        self,
        *,
        stage_label: str,
        prompt_input: str,
        client: OpenAI,
        system_prompt: str,
        text_param: dict | None,
        model: str,
        reasoning: str | None,
        previous_response_id: str | None = None,
        prompt_cache_key: str | None = None,
    ) -> dict:
        kwargs: dict[str, Any] = {"model": model, "instructions": system_prompt, "input": prompt_input}
        # if prompt_cache_key:
        #     kwargs["prompt_cache_key"] = prompt_cache_key
        if previous_response_id:
            kwargs["previous_response_id"] = previous_response_id
        if text_param:
            kwargs["text"] = text_param
        if reasoning:
            kwargs["reasoning"] = {"effort": reasoning}

        try:
            resp = client.responses.create(**kwargs)
        except Exception as exc:
            return {
                "status_code": None,
                "request_id": None,
                "body": None,
                "payload": None,
                "error": f"{stage_label} request failed: {exc}",
            }

        body = serialize_live_body(resp)
        payload, parse_error = _parse_output_payload(resp, body)
        request_id = getattr(resp, "id", None)
        if isinstance(body, dict) and not request_id:
            request_id = body.get("id")
        return {
            "status_code": 200,
            "request_id": request_id,
            "body": body,
            "payload": payload,
            "error": parse_error,
        }

    @staticmethod
    def _extract_labels(payload: dict | None) -> list[str]:
        if not payload:
            return []
        results = payload.get("results")
        if isinstance(results, list):
            return [str(item) for item in results if item is not None]
        return []

    @staticmethod
    def _should_continue(payload: dict | None) -> bool:
        if not payload:
            return False
        return payload.get("stop_reason") == "continue"

    def _build_l1_candidates(self, threat_l0_labels: list[str], mapping: dict) -> tuple[list[dict], dict[str, list]]:
        candidates: list[dict] = []
        l2_lookup: dict[str, list] = {}
        seen: set[str] = set()
        for label in threat_l0_labels:
            l0_entry = mapping.get("threats").get(label, {})
            for l1_name, l1_data in l0_entry.get("level1", {}).items():
                if not l1_name or l1_name in seen:
                    continue
                candidates.append({"name": l1_name, "desc": l1_data.get("examples", "")})
                seen.add(l1_name)
                l2_lookup[l1_name] = []
                for l2_name, l2_data in l1_data.get("level2", {}).items():
                    l2_lookup[l1_name].append({"name": l2_name, "desc": l2_data.get("examples", "")})
        return candidates, l2_lookup

    def _build_l2_candidates(self, threat_l1_labels: list[str], l2_lookup: dict[str, list]) -> list[dict]:
        candidates: list[dict] = []
        seen: set[str] = set()
        for l1_label in threat_l1_labels:
            # print(f"Looking up L2 for L1 label: {l1_label}")
            for l2 in l2_lookup.get(l1_label, []):
                # print(f"  Found L2 candidate: {l2}")
                name = l2.get("name")
                if not name or name in seen:
                    continue
                candidates.append({"name": name, "desc": l2.get("desc", "")})
                seen.add(name)
        # print(f"Final L2 candidates: {candidates}")
        return candidates

    def _run_threat_workflow(
        self,
        *,
        article_text: str,
        client: OpenAI,
        system_prompt: str,
        text_param: dict | None,
        mapping: dict,
        model: str,
        reasoning: str | None,
        custom_id: str,
        max_iterations: int = 5,
    ) -> dict:
        article_text = article_text or ""
        responses: dict[str, Any] = {"threat_l0": None, "threat_l1": None, "threat_l2": None}
        results_payload: dict[str, Any] = {"threat_l0": None, "threat_l1": None, "threat_l2": None}
        workflow_error: str | None = None
        iteration = 0
        workflow_active = True
        threat_l0_labels: list[str] = []
        threat_l1_labels: list[str] = []
        threat_l2_labels: list[str] = []
        previous_response_id: str | None = None
        l2_lookup: dict[str, list] = {}
        # shard = zlib.crc32(custom_id.encode("utf-8")) % 32
        shard= custom_id
        cache_key = f"threats_v1:shard_{shard}"

        while workflow_active and iteration < max_iterations:
            iteration += 1

            if not threat_l0_labels:
                prompt_input = f"ARTICLE_TEXT:\\n{article_text}"
                stage = self._call_stage(
                    stage_label="threat_l0",
                    prompt_input=prompt_input,
                    client=client,
                    system_prompt=system_prompt,
                    text_param=text_param,
                    model=model,
                    reasoning=reasoning,
                    previous_response_id=None,
                    prompt_cache_key=cache_key,
                )
                responses["threat_l0"] = stage
                results_payload["threat_l0"] = stage.get("payload")
                previous_response_id = stage.get("request_id") or previous_response_id
                if stage.get("error"):
                    workflow_error = stage["error"]
                    workflow_active = False
                    break
                threat_l0_labels = self._extract_labels(stage.get("payload"))
                workflow_active = bool(threat_l0_labels) and self._should_continue(stage.get("payload"))
                if not workflow_active:
                    break

            if not threat_l1_labels and workflow_active:
                l1_candidates, l2_lookup = self._build_l1_candidates(threat_l0_labels, mapping)

                # print(f"Threat L0 Labels: {threat_l0_labels}")
                # # print("mapping", mapping)
                # print(f"L1 Candidates: {l1_candidates}")
                # print(f"L2 Lookup: {l2_lookup}")
                # break

                if not l1_candidates:
                    threat_l1_data = {"results": ["No threat_l1 candidates found"], "stop_reason": "stop-manual"}
                    responses["threat_l1"] = {
                        "status_code": None,
                        "request_id": None,
                        "body": None,
                        "payload": threat_l1_data,
                        "error": None,
                    }
                    results_payload["threat_l1"] = threat_l1_data
                    workflow_active = False
                    break

                prompt_input = (
                    f"threats_l1_candidates:\\n{json.dumps(l1_candidates, indent=2)}"
                )
                stage = self._call_stage(
                    stage_label="threat_l1",
                    prompt_input=prompt_input,
                    client=client,
                    system_prompt=system_prompt,
                    text_param=text_param,
                    model=model,
                    reasoning=reasoning,
                    previous_response_id=previous_response_id,
                    prompt_cache_key=cache_key,
                )
                responses["threat_l1"] = stage
                results_payload["threat_l1"] = stage.get("payload")
                previous_response_id = stage.get("request_id") or previous_response_id
                if stage.get("error"):
                    workflow_error = stage["error"]
                    workflow_active = False
                    break
                threat_l1_labels = self._extract_labels(stage.get("payload"))
                workflow_active = bool(threat_l1_labels) and self._should_continue(stage.get("payload"))
                if not workflow_active:
                    break

            if not threat_l2_labels and workflow_active:
                threat_l2_candidates = self._build_l2_candidates(threat_l1_labels, l2_lookup)
                # print(f"--- Debugging L2 Candidates ---")
                # print(threat_l2_candidates)
                # print(f"Threat L0 Labels: {threat_l0_labels}")
                # # # print("mapping", mapping)
                # print(f"L1 Candidates: {l1_candidates}")
                # print(f"L2 Lookup: {l2_lookup}")
                # print(f"Threat L2 Labels: {threat_l2_candidates}")

                if not threat_l2_candidates:
                    threat_l2_data = {"results": ["No threat_l2 candidates found"], "stop_reason": "stop-manual"}
                    responses["threat_l2"] = {
                        "status_code": None,
                        "request_id": None,
                        "body": None,
                        "payload": threat_l2_data,
                        "error": None,
                    }
                    results_payload["threat_l2"] = threat_l2_data
                    workflow_active = False
                    break

                prompt_input = (
                    f"threats_l2_candidates:\\n{json.dumps(threat_l2_candidates, indent=2)}"
                )
                stage = self._call_stage(
                    stage_label="threat_l2",
                    prompt_input=prompt_input,
                    client=client,
                    system_prompt=system_prompt,
                    text_param=text_param,
                    model=model,
                    reasoning=reasoning,
                    previous_response_id=previous_response_id,
                    prompt_cache_key=cache_key,
                )
                responses["threat_l2"] = stage
                results_payload["threat_l2"] = stage.get("payload")
                previous_response_id = stage.get("request_id") or previous_response_id
                if stage.get("error"):
                    workflow_error = stage["error"]
                threat_l2_labels = self._extract_labels(stage.get("payload"))
                workflow_active = False

            if threat_l0_labels and threat_l1_labels and threat_l2_labels:
                break

        if workflow_active and iteration >= max_iterations:
            workflow_error = f"Max iterations reached ({max_iterations})."

        return {
            "id": f"{self.name}_live_{uuid4().hex}",
            "custom_id": custom_id,
            "responses": responses,
            "results_payload": results_payload,
            "error": {"message": workflow_error} if workflow_error else None,
            "iterations": iteration,
        }


DRIVER_TASK = SimpleTask(name="driver", prompt_key="classify_direct_driver", output_prefix="drivers")
GEOGRAPHY_TASK = SimpleTask(name="geography", prompt_key="classify_region", output_prefix="geography")
TAXA_TASK = SimpleTask(name="taxa", prompt_key="classify_taxa", output_prefix="taxa")
STUDY_TASK = SimpleTask(name="study", prompt_key="classify_study", output_prefix="study")
ECOSYSTEM_TASK = EcosystemTask(name="ecosystems", prompt_key="classify_ecosystem_typology", supports_batch=False, output_prefix="ecosystems")
THREAT_TASK = ThreatTask(name="threats", prompt_key="classify_threats", supports_batch=False, output_prefix="threats")

TASK_ALIASES = {
    "driver": DRIVER_TASK,
    "drivers": DRIVER_TASK,
    "direct_driver": DRIVER_TASK,
    "direct_drivers": DRIVER_TASK,
    "geography": GEOGRAPHY_TASK,
    "geo": GEOGRAPHY_TASK,
    "region": GEOGRAPHY_TASK,
    "regions": GEOGRAPHY_TASK,
    "taxa": TAXA_TASK,
    "study": STUDY_TASK,
    "studies": STUDY_TASK,
    "ecosystems": ECOSYSTEM_TASK,
    "ecosystem": ECOSYSTEM_TASK,
    "ecosystem_typology": ECOSYSTEM_TASK,
    "typology": ECOSYSTEM_TASK,
    "threat": THREAT_TASK,
    "threats": THREAT_TASK,
    "threat_l0": THREAT_TASK,
    "threat_classification": THREAT_TASK,
}


def get_task(name: str) -> TaskDefinition:
    key = (name or "").lower().strip()
    if key not in TASK_ALIASES:
        raise ValueError(f"Unknown task '{name}'. Available tasks: {', '.join(sorted(set(TASK_ALIASES)))}")
    return TASK_ALIASES[key]


def available_task_names() -> list[str]:
    return sorted({task.name for task in TASK_ALIASES.values()})
