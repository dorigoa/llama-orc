from dataclasses import dataclass, field
from pathlib import Path
from object_models import Model
import persist
from config_manager import get_settings

settings = get_settings()
    
_AVAILABLE_MODELS: list[Model] = []

#_____________________________________________________________________________
def get_model_by_name( name: str ) -> Model:
    for model in _AVAILABLE_MODELS:
        if name == model.model_name:
            return model
    return None
    
#_____________________________________________________________________________
def get_last_started_model( ) -> Model:
    for m in _AVAILABLE_MODELS:
        if m.last_started:
            return m
    return _AVAILABLE_MODELS[0]
    
#_____________________________________________________________________________
def get_available_model_names( refresh: bool = False ) -> list[str]:
    #global _AVAILABLE_MODELS
    # if refresh:
    #     _AVAILABLE_MODELS = _discover_available_models( )
    # names = []
    # for m in get_available_models():#_AVAILABLE_MODELS:
    #     names.append( m.model_name )
    # return names
    return [m.model_name for m in get_available_models(refresh)]

#_____________________________________________________________________________
def get_available_models( refresh: bool = False ) -> list[Model]:
    global _AVAILABLE_MODELS
    if refresh:
        _AVAILABLE_MODELS = _discover_available_models( )
    return _AVAILABLE_MODELS

#_____________________________________________________________________________
def _discover_available_models( ) -> list[Model]:

    #
    # First: model base dir (defined in settings) is scanned
    # Second: persist json file is scanned
    # 
    # If a model from persist file is in the list models retrieved from dir
    # extra params are set, otherwise settings defaults are used.

    # READ available models from dir
    root = Path(settings.MODEL_BASE_DIR)
    if not root.is_dir():
        return []
    model_list = sorted(
        (p for p in root.iterdir() if p.is_dir()),
        key=lambda p: p.name.lower()
    )

    models = []

    # READ models extra param from persist
    data = persist.get_params_handler().load_params()


    for m in model_list:
        pmmproj = _find_mmproj_file( m )
        #if pmmproj:
        #    mmproj = pmmproj
        #else:
        #    mmproj = None

        if m.name in data:
            M = Model(
                model_name    = m.name,
                model_path    = m / f"{m.name}.gguf",
                mmproj_path   = pmmproj,
                ctxsize       = data[m.name]['context_size'],
                temperature   = data[m.name]['temperature'],
                top_p         = data[m.name]['top_p'],
                top_k         = data[m.name]['top_k'],
                shard_balance = data[m.name]['shard_balance'],
                last_started  = data[m.name]['last_started']
            )
        else:
            M = Model(
                model_name      = m.name,
                model_path      = m / f"{m.name}.gguf",
                mmproj_path     = pmmproj,
                ctxsize         = settings.DEFAULT_CONTEXT_SIZE,
                temperature     = settings.DEFAULT_TEMP,
                top_p           = settings.DEFAULT_TOP_P,
                top_k           = settings.DEFAULT_TOP_K,
                shard_balance   = "1,1",
                last_started    = False
            )
        models.append(M)

    return models

#_____________________________________________________________________________
def _find_mmproj_file(directory: str | Path) -> Path | None:
    base = Path(directory)
    for p in base.iterdir():
        if p.is_file() and p.name.startswith("mmproj"):
            return p
    return None

#_____________________________________________________________________________
# def default_context_size_for_model(model_name: Optional[str]) -> int:
#     """Return model-specific ctxsize when configured, otherwise global default."""
#     if model_name and model_name in AVAILABLE_MODELS:
#         model_ctx = _get_configured_value( AVAILABLE_MODELS[model_name], "ctxsize", int, 8192)
#         if model_ctx > 0:
#             return model_ctx
#     return settings.DEFAULT_CONTEXT_SIZE#int(getattr(settings, "DEFAULT_CONTEXT_SIZE", 32768))

# #_____________________________________________________________________________
# def default_temp_for_model(model_name: Optional[str]) -> float:
#     """Return model-specific temperature when configured, otherwise global default."""
#     if model_name and model_name in AVAILABLE_MODELS:
#         model_temp = _get_configured_value(AVAILABLE_MODELS[model_name], "temperature", float, 0.3)
#         if model_temp > 0:
#             return model_temp
#     return settings.DEFAULT_TEMP

# #_____________________________________________________________________________
# def default_top_p_for_model(model_name: Optional[str]) -> float:
#     """Return model-specific top_p when configured, otherwise global default."""
#     if model_name and model_name in AVAILABLE_MODELS:
#         model_top_p = _get_configured_value(AVAILABLE_MODELS[model_name], "top_p", float, 0.5)
#         if model_top_p > 0:
#             return model_top_p
#     return settings.DEFAULT_TOP_P

# #_____________________________________________________________________________
# def default_top_k_for_model(model_name: Optional[str]) -> int:
#     """Return model-specific top_k when configured, otherwise global default."""
#     if model_name and model_name in AVAILABLE_MODELS:
#         model_top_k = _get_configured_value(AVAILABLE_MODELS[model_name], "top_k", int, 30)
#         if model_top_k > 0:
#             return model_top_k
#     return settings.DEFAULT_TOP_K

# #_____________________________________________________________________________
# def default_shard_balance_for_model(model_name: Optional[str]) -> str:
#     """Return shard_balance (which depends on the cluster) when configured, otherwise global default."""
#     if model_name and model_name in AVAILABLE_MODELS:
#         model_shard_balance = _get_configured_value(AVAILABLE_MODELS[model_name], "shard_balance", str, "1,1")
#         if model_shard_balance:
#             return model_shard_balance
#     return settings.DEFAULT_SHARD_BALANCE

#_____________________________________________________________________________
# def configured_model_path(configured: Any) -> str:
#     """Extract the main GGUF path/folder from one AVAILABLE_MODELS value.

#     Supports both legacy string values and dict values, for example:
#         "Model": "/path/to/model.gguf"
#         "Model": {"model": "/path/to/model.gguf", "mmproj": "/path/to/mmproj.gguf"}
#     """
#     if isinstance(configured, (str, Path)):
#         return str(configured)

#     if isinstance(configured, dict):
#         # Prefer explicit main-model keys. Do not pick mmproj unless it is the only usable path.
#         preferred_keys = (
#             "model",
#             "model_path",
#             "path",
#             "gguf",
#             "file",
#             "filename",
#             "model_file",
#             "folder",
#             "directory",
#             "dir",
#         )
#         for key in preferred_keys:
#             value = configured.get(key)
#             if isinstance(value, (str, Path)) and str(value).strip():
#                 return str(value)

#         # Fallback: first string/path value that does not look like a multimodal projector.
#         for value in configured.values():
#             if isinstance(value, (str, Path)) and str(value).strip():
#                 candidate = str(value)
#                 if "mmproj" not in Path(candidate).name.lower():
#                     return candidate

#         # Last resort: any string/path value, including mmproj.
#         for value in configured.values():
#             if isinstance(value, (str, Path)) and str(value).strip():
#                 return str(value)

#     raise TypeError(f"Unsupported AVAILABLE_MODELS entry: {configured!r}")

#_____________________________________________________________________________
# def path_to_model_folder(path_string: str | Path) -> Path:
#     """Accept either a GGUF file path or a model directory path."""
#     p = Path(path_string).expanduser()

#     # Path.exists() is intentionally not required here because network volumes may be late-mounted.
#     # If the configured string ends with .gguf, treat it as a model file and use its parent.
#     if p.suffix.lower() == ".gguf":
#         return p.parent.resolve()

#     return p.resolve()

# #_____________________________________________________________________________
# def extract_model_from_props(payload: dict[str, Any]) -> Optional[str]:
#     for key in ("model_path", "model", "model_name", "model_alias"):
#         value = payload.get(key)
#         if isinstance(value, str) and value.strip():
#             return value.strip()
#     return None

# #_____________________________________________________________________________
# def extract_model_from_openai_models(payload: dict[str, Any]) -> Optional[str]:
#     """Extract model id/name from /v1/models compatible response."""
#     data = payload.get("data")
#     if isinstance(data, list) and data:
#         first = data[0]
#         if isinstance(first, dict):
#             model_id = first.get("id") or first.get("name")
#             if isinstance(model_id, str) and model_id.strip():
#                 return model_id.strip()
#     return None

_AVAILABLE_MODELS: list[Model] = _discover_available_models( )