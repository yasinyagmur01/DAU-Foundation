# Koşum Yolu Denetimi — 2026-08-09

⚠ **Bu denetim 2026-08-09 tarihlidir; iki sabit adı o tarihten sonra değişti.**
`NLI_FILTER_STATS` → `POLARITY_FILTER_STATS` ve polarite kapısı NLI'dan kosinüse
geçti (**D-032**); `PREF_LIVED_CONTEXT_TEMPLATE` **emekli edildi** (**D-032**) —
çift prompt'u artık kararın verildiği prompt'un kendisi. Aşağıdaki tablolar
eski adları taşıyor; **bulgular geçerli, isimler değil.**

Giriş noktası: `dau/diagnostics/run_cprime_multigen.py::main()`

Kapsam (Görev 0 — çağrı grafiğinden türeyen dosyalar; test dosyaları hariç):

| # | dosya | satır | koşul |
|---|---|---:|---|
| 1 | `dau/diagnostics/run_cprime_multigen.py` | 792 | always |
| 2 | `dau/diagnostics/run_protocol_c_prime.py` | 1280 | always (helpers only) |
| 3 | `dau/foundation/graph.py` | 1447 | always |
| 4 | `dau/foundation/meta_observer.py` | 358 | always |
| 5 | `dau/foundation/self_model.py` | 203 | always |
| 6 | `dau/foundation/generation.py` | 388 | always |
| 7 | `dau/foundation/state.py` | 477 | always |
| 8 | `dau/foundation/constraints.py` | 144 | always |
| 9 | `dau/foundation/delta.py` | 163 | always |
| 10 | `dau/foundation/drift.py` | 129 | always |
| 11 | `dau/foundation/emotional_weight.py` | 188 | always |
| 12 | `dau/foundation/lod.py` | 169 | always |
| 13 | `dau/foundation/social.py` | 237 | always |
| 14 | `dau/foundation/time_model.py` | 110 | always |
| 15 | `dau/foundation/memory_bridge.py` | 113 | always |
| 16 | `dau/foundation/semantic_similarity.py` | 127 | always |
| 17 | `dau/foundation/lora_update.py` | 453 | always (lived examples; train if LoRA) |
| 18 | `dau/generation/fitness.py` | 100 | always |
| 19 | `dau/society/environment.py` | 159 | always |
| 20 | `dau/society/extraction.py` | 116 | always |
| 21 | `dau/memory/__init__.py` | 50 | always |
| 22 | `dau/memory/store.py` | 560 | always |
| 23 | `dau/memory/retrieval.py` | 149 | always |
| 24 | `dau/memory/decay.py` | 86 | always |
| 25 | `dau/memory/ppr_retrieval.py` | 120 | always |
| 26 | `dau/foundation/nli_filter.py` | 57 | conditional: LoRA train pair build |
| 27 | `dau/foundation/local_llm.py` | 754 | conditional: backend=local and/or LoRA train |
| 28 | `dau/foundation/llm_backend.py` | 79 | conditional: DAU_LLM_BACKEND=local |

Stream döngüsü (her event): `social_pre_node` → `agent_node` → `evaluator_node` → `meta_observer_node` → `pool_step_node` → `should_continue`.

Not: `run_protocol_c_prime.py` yalnızca multigen'in import ettiği yardımcılar üzerinden kapsanır (`_collect_pe_events` / `run_arm` / stats / checkpoint yolu değil).

---

## K1 — Sessiz devam yolları

| dosya:satır | desen | tetikleyen koşul | ne döner | çağıran ne yapar |
|---|---|---|---|---|
| run_cprime_multigen.py:560-563 | `except Exception: pass` | `store.close()` raises | yutulan (None) | `run_lineage` finally → `tmp.cleanup()` |
| run_cprime_multigen.py:565-568 | `except Exception: pass` | `tmp.cleanup()` raises | yutulan (None) | `run_lineage` biter; try gövdesi başarılıysa sonuç zaten dönmüş |
| run_cprime_multigen.py:361-362 | tip fallback | `heir.drift_state` `DriftState` değil | boş `DriftState()` | `birth_drift_flags`/`magnitudes` boş default'tan |
| run_cprime_multigen.py:337-338 | `.get(MARKER_*, 0.0)` | somatic marker yok | `0.0` | `consolidate_generation` reward/threat |
| run_cprime_multigen.py:647-649 | `if not gated: append` atlama | `gen2['gated']` truthy | listeye eklenmez | `summary.mean_gen2_pe_by_gen1_arm` / `n_usable_gen2_*` |
| run_cprime_multigen.py:649 | `.get('n_transfer_candidates', 0)` | anahtar yok | `0` | `summary.n_transfer_candidates_total` |
| run_cprime_multigen.py:715 | `.get('mean_pe')` | anahtar yok | `None` → `delta_pe` | JSON `gen2.delta_pe` |
| run_protocol_c_prime.py:252-253 | erken return `EMPTY_MEAN` | `_mean` boş liste | `0.0` | `_window_mean` → pe_before/pe_after/mean_pe |
| run_protocol_c_prime.py:268-269 | erken return `EMPTY_MEAN` | `_window_mean` boş pe_list | `0.0` | gen1/gen2 window mean |
| run_protocol_c_prime.py:382-383 | `continue` örnek atla | completion boş veya `== COMPLETION_FALLBACK` | örnek dışarıda | `_phase1_diversity` n_unique/pes azalır |
| run_protocol_c_prime.py:388 | ternary `EMPTY_MEAN` | `len(pes) < 2` | `pe_gap_max=0.0` | diversity gate girdisi |
| run_protocol_c_prime.py:428-429 | `except ImportError: return` | torch yok | no-op | `_lock_seeds` random/np/env devam |
| run_protocol_c_prime.py:442-443 | `except Exception: pass` | cudnn attr set fail | devam | `use_deterministic_algorithms` çağrılır |
| run_protocol_c_prime.py:570-573 | `except ValueError` hash fallback | `agent_id` trailing int değil | `abs(hash(agent_id)) % 2**31` | shuffle seed (`_seed_from_agent_id`) |
| run_protocol_c_prime.py:590-591 | `except ImportError: return []` | `lora_update` import fail | `[]` | lived_examples boş → diversity/train boş |
| run_protocol_c_prime.py:561-562 | pad zeros | pe_list boş | `[0.0]*n_events` | `_window_mean` → `0.0` |
| run_protocol_c_prime.py:697-704 | erken return `(0,0)` log yok | `DAU_LORA_ENABLED` truthy değil | `(0,0)` | n_pairs_trained/rejected=0; phase-2 devam |
| run_protocol_c_prime.py:713-714 | `except ImportError: return (0,0)` log yok | train import fail | `(0,0)` | arm eğitimsiz devam |
| run_protocol_c_prime.py:721-724 | `except Exception: return (0,0)` log yok | `build_pe_ranked_pairs` raises | `(0,0)` | arm eğitimsiz; phase-2 devam |
| run_protocol_c_prime.py:740-748 | `except Exception` + WARN print | `run_micro_train_preference_step` raises | `(0,0)` | WARN; arm devam |
| run_protocol_c_prime.py:750-757 | `if not trained: return (0,0)` + WARN | `result['trained']` false/missing | `(0,0)` | WARN + reason; arm devam |
| run_protocol_c_prime.py:731 | `if shuffled and pairs:` | pairs boş | shuffle atlanır | train `[]` ile çağrılır → genelde trained=False |
| graph.py:106-113 | `except ImportError` stub | `local_llm` import yok | `switch_adapter`/`get_loaded_model` → `None` | `agent_node` local hot-swap atlar |
| graph.py:311-312 | erken return | `.env` dosya değil | None (no-op) | `load_env_file`/`_build_llm` devam |
| graph.py:315-316 | `continue` | boş/`#`/`=` yok satır | satır atlanır | sonraki satır |
| graph.py:320-321 | skip set | `key in os.environ` | yazılmaz | mevcut env korunur |
| graph.py:518 | `return None` | outcome key yok/boş | `None` | `_past_outcomes` o entry atlar |
| graph.py:533-535 | erken `[]` | `k <= 0` | `[]` | memory expected boş → fallback şablon |
| graph.py:546-550 | erken `[]` | `MEMORY_ENABLED=False` veya store yok | `[]` | `resolve_expected_outcome` → fallback |
| graph.py:560-561 | `except Exception: return []` log yok | `retrieve_relevant` herhangi hata | `[]` | fallback şablon |
| graph.py:563-564 | erken `[]` | memories boş | `[]` | fallback şablon |
| graph.py:568-569 | `continue` | entry `dict` değil | atlanır | diğer entry |
| graph.py:813-814 | erken `{}` | `opponent_id` falsy | `{}` | LangGraph state değişmez |
| graph.py:876-878 | memories=`[]` | MEMORY off / store yok | boş liste | prompt'a memory bloğu yok |
| graph.py:924-926 | skip if | `get_loaded_model() is None` | hot-swap yok | `LocalBackend.complete` yine çağrılır |
| graph.py:973-974 | erken `{}` | `event_log` boş | `{}` | PE/delta yazılmaz; meta/pool devam |
| graph.py:991-993 | `except Exception` log yok | `compute_precision_weight`/`apply_precision_weighting` hata | `precision_weight=1.0`, `precision_pe=raw_pe` | PE path devam |
| graph.py:1065-1072 | skip write | MEMORY off / store yok / decision None / persist falsy | `_memory_written` artmaz | evaluator state günceller |
| graph.py:1091-1094 | erken `{}` | `env_state` yok/yanlış veya `event_log` boş | `{}` | pool/crisis uygulanmaz |
| meta_observer.py:82-86 | `return None` | score key yok | `None` | `context_prune` entry tutar |
| meta_observer.py:97-98 | variance=`METRIC_MIN` | `len(scores) < 2` | `0.0` | prune eşiği aşılmaz |
| meta_observer.py:146-152 | empty frozenset | delta yok / trauma / mag < HEAL_THRESHOLD | `frozenset()` | meta heal skip-set boş |
| meta_observer.py:216-217 | `continue` | prune'da non-dict | atlanır | diğerleri |
| meta_observer.py:239-247 | erken copy | heal koşulu false | drift kopyası | heal yok |
| meta_observer.py:259-264 | `continue` | flag false / domain invalid / skip-set | o domain heal edilmez | döngü devam |
| meta_observer.py:281-289 | erken context | m_ratio/delta kapısı veya store unbound | context değişmez | retrieval eklenmez |
| self_model.py:126-127 | empty EW | `delta_log` boş | `EmotionalWeight()` | `m_ratio`/`f_agent` hesaplanır |
| self_model.py:136-137 | `continue` | non-dict retrieval entry | atlanır | scores kısa |
| self_model.py:150-153 | default pool | `env_state` EnvironmentState değil | `delta_pool=0.0` | `compute_fitness` devam |
| generation.py:98-109 | `continue` | legacy filtre fail | aday düşer | selected kısa |
| generation.py:133-167 | `continue` | recall/`w_transfer`/drift kapısı | aday düşer | selected kısa |
| generation.py:195-196 | erken `[]` | `memory_store is None` | `[]` | `inherited_memories=[]` |
| generation.py:201-215 | reconstruct | `get_record_payload` None | minimal `DeltaRecord` | skorlama devam |
| generation.py:258-259 | default DriftState | drift tipi yanlış | boş DriftState | transfer drift boş |
| generation.py:300-304 | erken `{}` | store None veya `seed_inherited_record` yok | `id_map={}` | context parent_id |
| generation.py:311-312 | skip map | `new_id` falsy | o parent map'lenmez | `id_map.get` → parent_id |
| emotional_weight.py:127 | `continue` | entry not dict | atlanır | somatic scale döngüsü |
| emotional_weight.py:129 | `continue` | `INHERITED_WARNING_KEY` falsy | atlanır | scale uygulanmaz o entry'ye |
| emotional_weight.py:133-134 | erken return | scales boş | `ew` değişmez | caller EW kullanır |
| memory_bridge.py:55-56 | erken `None` | `store is None` | `None` | yazım yok |
| memory_bridge.py:76-77 | erken `[]` | `store is None` | `[]` | retrieval boş |
| memory_bridge.py:89 | `continue` | `get_node` None | atlanır | result listesi kısa |
| lora_update.py:163 | `continue` | `event_type != agent_decision` | atlanır | lived examples |
| lora_update.py:167 | `continue` | decision payload None | atlanır | lived examples |
| lora_update.py:287 | `continue` | `abs(pe_left-pe_right) < PE_RANK_MIN_GAP` | çift düşer | pairs kısa |
| lora_update.py:295 | `continue` | empty veya chosen==rejected | çift düşer | pairs kısa |
| lora_update.py:299 | `continue` | NLI polarity false | çift düşer; stats++ | pairs kısa |
| lora_update.py:369-375 | erken return skip dict | `is_lora_enabled()` false | `trained=False, skipped=True` | `_train_adapter` trained=False yolu |
| lora_update.py:413-420 | erken skip | `not examples` | skip result | train yok |
| semantic_similarity.py:47-48 | `except Exception` retry | `local_files_only=True` load fail | Hub download retry | `_load_model` |
| semantic_similarity.py:61-64 | erken similarity | boş metin çiftleri | `1.0` veya `0.0` | PE = 1-sim |
| semantic_similarity.py:108-109 | erken `1.0` | `len(history) < PRECISION_MIN_HISTORY` | `1.0` | precision weight cold-start |
| store.py:352-353 | `continue` | Chroma `doc is None` | atlanır | payload listesi |
| store.py:482-485 | `except Exception: pass` | `collection.delete` fail | yutulan | `delete_record` devam (SQLite tarafı) |
| retrieval.py:73-76 | `except Exception: ppr=0.0` | `ppr_score_for_domain` hata | `ppr=0.0` | memory_score formülüne girer |
| ppr_retrieval.py:68-69 | `continue` | `src == dst` | edge atlanır | graf yükleme |
| ppr_retrieval.py:91-92 | erken `{seed:1.0}` | networkx yok | `{seed_domain: 1.0}` | `ppr_score_for_domain` |
| ppr_retrieval.py:95-96 | erken `{seed:1.0}` | `len(G.nodes)==0` | `{seed_domain: 1.0}` | aynı |
| ppr_retrieval.py:106-107 | `except Exception: return {seed:1.0}` | pagerank fail | `{seed_domain: 1.0}` | aynı |
| nli_filter.py:40-41 | erken `0.0` | `NLI_ENABLED` false | `0.0` | contradiction_score |
| nli_filter.py:55-56 | erken `True` | `NLI_ENABLED` false | `True` (polarity geç) | tüm çiftler geçer |
| local_llm.py:153-156 | `except Exception` fallback | 4-bit load fail | full-precision CPU load | `load_local_model` |
| local_llm.py:177-181 | `except Exception: pass` | `disable()` fail | yutulan | adapter disable yolu |
| local_llm.py:208-215 | `except Exception` manuel zero | `reset_lora_parameters` fail | `lora_B.zero_()` | reset devam |
| local_llm.py:265-267 | `except Exception` warning+return | `save_pretrained` fail | return (save skip) | adapter disk'e yazılmaz |
| local_llm.py:318-321 | `except Exception: pass` | `enable()` fail | yutulan | switch_adapter |
| local_llm.py:324-327 | `except Exception: pass` | `set_adapter` fail | yutulan | switch_adapter |
| local_llm.py:336-339 | `except Exception` warning+reset | switch_adapter outer fail | `_active_agent_id=None` | infer devam edebilir adaptersız |
| local_llm.py:373-378 | `except Exception` fallback | `apply_chat_template` fail | plain template | generate_completion |
| local_llm.py:539-546 | `except TypeError/Exception: continue` | gradient checkpointing setup fail | modül atlanır | train devam |
| local_llm.py:561-564 | `except Exception: pass` | `enable_adapter_layers` fail | yutulan | DPO setup |
| local_llm.py:568-571 | `except Exception: pass` | `set_adapter` fail | yutulan | DPO setup |
| local_llm.py:647-648 | `continue` | `batch_loss is None` | step atlanır | DPO epoch loop |
| local_llm.py:726-734 | `except Exception` warning+dict | DPO train fail | `trained=False` dict | `_train_adapter` WARN yolu |
| local_llm.py:688-694 | erken skip dict | LoRA kapalı | `trained=False, reason=DAU_LORA_ENABLED=0` | `_train_adapter` |
| local_llm.py:697-703 | erken skip dict | `active is None` | `reason=no loaded model` | `_train_adapter` |
| local_llm.py:706-712 | erken skip dict | `pair_count==0` | `reason=no preference pairs` | `_train_adapter` |
| local_llm.py:715-722 | erken skip dict | `tokenizer is None` | `reason=no tokenizer` | `_train_adapter` |

## K2 — Ortam değişkenleri

### K2a — `os.environ.get` / `getenv`

| dosya:satır | değişken | default | default'ta davranış |
|---|---|---|---|
| run_cprime_multigen.py:86 | DAU_MULTIGEN_N_PAIRS | "15" → N_PAIRS=15 | CLI/run default pair count |
| run_cprime_multigen.py:87 | DAU_MULTIGEN_EVENTS_GEN1 | "50" | gen1 events/phase |
| run_cprime_multigen.py:88 | DAU_MULTIGEN_EVENTS_GEN2 | "20" | gen2 events |
| run_cprime_multigen.py:89 | DAU_MULTIGEN_K_GEN2 | "3" | gen2 n_unique floor |
| run_cprime_multigen.py:90 | DAU_MULTIGEN_SEED_START | "2001" | first seed |
| run_cprime_multigen.py:91-93 | DAU_MULTIGEN_PE_WINDOW | str(PE_WINDOW_EVENTS)="10" | gen2 window mean length |
| run_cprime_multigen.py:96-100 | DAU_MULTIGEN_RESULTS | "dau_runs/protocol_c_prime_multigen_results.json" | default JSON path |
| run_cprime_multigen.py:205 | DAU_MULTIGEN_MOCK_LLM | "0" | mock off unless 1/true/TRUE/yes/YES |
| run_cprime_multigen.py:692 | DAU_LORA_ENABLED | "0" | JSON alanı `lora_enabled` (rapor) |
| run_cprime_multigen.py:693 | DAU_NLI_FILTER_ENABLED | "1" | JSON alanı `nli_filter_enabled` (rapor) |
| run_protocol_c_prime.py:73 | DAU_LLM_TEMPERATURE | "0.2" → TEMPERATURE | import-time; `_lock_seeds` env'e yazar |
| run_protocol_c_prime.py:148 | DAU_TORCH_THREADS | "14" | `torch.set_num_threads` if torch |
| run_protocol_c_prime.py:445 | DAU_LLM_DO_SAMPLE | "0" | truthy → warn_only=False deterministic algs |
| run_protocol_c_prime.py:697 | DAU_LORA_ENABLED | "0" | train skip → (0,0) |
| graph.py:389-391 | DAU_LLM_TEMPERATURE | "" → TEMPERATURE=0.2 | Groq/ChatGroq temperature |
| graph.py:398-400 | DAU_LLM_SEED | "" → None | model_kwargs'a seed eklenmez |
| graph.py:407-410 | DAU_LLM_BACKEND | "groq" | `"local"` değilse Groq path |
| graph.py:417-422 | GROQ_API_KEY | "" | boş → RuntimeError (sessiz değil) |
| lora_update.py:125 | DAU_LORA_ENABLED | "0" | `is_lora_enabled()` → False |
| nli_filter.py:18 | DAU_NLI_FILTER_ENABLED | "1" (`!= "0"`) | "0" → skor 0.0, polarity True |
| local_llm.py:47-75 | DAU_LLM_DO_SAMPLE | "0" | greedy decode |
| local_llm.py:48-75 | DAU_LLM_TEMPERATURE | str(0.0) | parse fail/≤floor → greedy |
| local_llm.py:49,419-423 | DAU_LLM_SEED | "0" | do_sample iken per-call seed; ValueError→0 |
| llm_backend.py:68-71 | DAU_LLM_BACKEND | "groq" | yalnızca "local" → LocalBackend |

### K2b — `os.environ[...] =` / `setdefault`

| dosya:satır | işlem | değişken | değer | etki |
|---|---|---|---|---|
| run_cprime_multigen.py:215 | setdefault | DAU_LLM_BACKEND | "groq" | mock install; yalnızca unset ise |
| run_cprime_multigen.py:759 | = | DAU_MULTIGEN_MOCK_LLM | "1" | CLI --mock-llm |
| run_protocol_c_prime.py:431-434 | setdefault | CUBLAS_WORKSPACE_CONFIG | ":4096:8" | torch import başarılıysa |
| run_protocol_c_prime.py:459 | = | DAU_LLM_SEED | str(seed) | her `_lock_seeds` |
| run_protocol_c_prime.py:460 | = | DAU_LLM_TEMPERATURE | str(TEMPERATURE) | import-time TEMPERATURE ile overwrite |
| run_protocol_c_prime.py:716 | setdefault | DAU_NLI_FILTER_ENABLED | "1" | LORA train path girildiyse |
| graph.py:320-321 | = (if absent) | .env KEY | dosyadan value | `key not in os.environ` iken |

## K3 — Sabitler

| ad | değer | tanım | tüketim | constraints_dışı? |
|---|---|---|---|---|
| N_PAIRS | env/15 | run_cprime_multigen.py:86 | run_cprime_multigen/CLI/JSON | evet |
| EVENTS_GEN1 | env/50 | run_cprime_multigen.py:87 | gen1 lives/CLI/JSON | evet |
| EVENTS_GEN2 | env/20 | run_cprime_multigen.py:88 | gen2/CLI/JSON | evet |
| K_GEN2 | env/3 | run_cprime_multigen.py:89 | gen2 diversity gate | evet |
| SEED_START | env/2001 | run_cprime_multigen.py:90 | seed range | evet |
| PE_WINDOW_GEN2 | env/PE_WINDOW_EVENTS | run_cprime_multigen.py:91-93 | gen2 _window_mean | evet |
| MOCK_LLM_ENV | "DAU_MULTIGEN_MOCK_LLM" | run_cprime_multigen.py:94 | mock enable | evet |
| MOCK_LLM_DEFAULT | "0" | run_cprime_multigen.py:95 | default mock off | evet |
| RESULTS_PATH | env path / default json | run_cprime_multigen.py:96-101 | write default | evet |
| PROTOCOL_ID | "C_PRIME_MULTIGEN" | run_cprime_multigen.py:103 | JSON protocol | evet |
| HEIR_SUFFIX | "g2" | run_cprime_multigen.py:104 | heir_agent_id | evet |
| PARENT_SUFFIX | "g1" | run_cprime_multigen.py:105 | parent_agent_id | evet |
| TMP_PREFIX | "dau_cprime_multigen_" | run_cprime_multigen.py:106 | tempdir | evet |
| MOCK_DECISION_TEXTS | 5-tuple strings | run_cprime_multigen.py:108-114 | MockLLM | evet |
| GEN2_DIVERSITY_MIN_PE_GAP | 1e-6 (alias) | run_cprime_multigen.py:117 | gen2 pe_gap gate | evet |
| AB_ENERGY_FLOOR | 0.15 | run_protocol_c_prime.py:97 / graph.py:126 | should_continue; multigen monkeypatch | evet |
| EMPTY_COUNT | 0 | run_protocol_c_prime.py:102 | pair counters/train returns | evet |
| EMPTY_MEAN | 0.0 | run_protocol_c_prime.py:103 | empty means/pe_gap/pad | evet |
| MIN_TRACE_FRACTION | 0.5 | run_protocol_c_prime.py:99 | _pad_pe_list warn | evet |
| DIVERSITY_MIN_UNIQUE | 5 | run_protocol_c_prime.py:129 | gen1 diversity gate | evet |
| DIVERSITY_MIN_PE_GAP | 1e-6 | run_protocol_c_prime.py:130 | gen1/gen2 gap | evet |
| PE_WINDOW_EVENTS | 10 | run_protocol_c_prime.py:131 | gen1 window; JSON pe_window_gen1 | evet |
| NAN_DELTA | float("nan") | run_protocol_c_prime.py:132 | gated gen1 delta_pe | evet |
| TEMPERATURE | env/0.2 | run_protocol_c_prime.py:73 / graph.py:131 | _lock_seeds write; LLM fallback | evet |
| LORA_ENABLED_ENV | "DAU_LORA_ENABLED" | run_protocol_c_prime.py:137 / lora_update.py:29 | train gate + JSON | evet |
| NLI_FILTER_ENABLED_ENV | "DAU_NLI_FILTER_ENABLED" | run_protocol_c_prime.py:138 | setdefault + JSON | evet |
| LLM_TEMPERATURE_ENV | "DAU_LLM_TEMPERATURE" | run_protocol_c_prime.py:134 | _lock_seeds / resolve | evet |
| LLM_SEED_ENV | "DAU_LLM_SEED" | run_protocol_c_prime.py:135 | _lock_seeds / resolve | evet |
| LLM_DO_SAMPLE_ENV | "DAU_LLM_DO_SAMPLE" | run_protocol_c_prime.py:136 / local_llm.py:47 | determinism/sampling | evet |
| LLM_DO_SAMPLE_TRUTHY | frozenset | run_protocol_c_prime.py:143 | sampling detect | evet |
| TORCH_THREADS_ENV | "DAU_TORCH_THREADS" | run_protocol_c_prime.py:139 | threads env | evet |
| TORCH_NUM_THREADS | env/14 | run_protocol_c_prime.py:148 | torch.set_num_threads | evet |
| CUBLAS_WORKSPACE_CONFIG_ENV | "CUBLAS_WORKSPACE_CONFIG" | run_protocol_c_prime.py:140 | setdefault | evet |
| CUBLAS_WORKSPACE_CONFIG_VALUE | ":4096:8" | run_protocol_c_prime.py:142 | setdefault value | evet |
| TORCH_DETERMINISTIC_WARN_ONLY | True | run_protocol_c_prime.py:151 | use_deterministic_algorithms | evet |
| STREAM_NODES_PER_EVENT | 5 | run_protocol_c_prime.py:153 | stream_limit | evet |
| STREAM_RECURSION_HEADROOM | 40 | run_protocol_c_prime.py:158 | stream_limit | evet |
| NICHE_*_RANGE (4) | scarcity/uncertainty/social/time ranges | run_protocol_c_prime.py:165-168 | _seed_niche | evet |
| NICHE_POOL_FRACTION_RANGE | (0.40, 1.00) | run_protocol_c_prime.py:171 | _seed_niche; import assert | evet |
| OPPONENT_ID | "cprime-npc-opponent" | run_protocol_c_prime.py:173 | _initial_state | evet |
| ARM_LIVED/NULL/SHUFFLE / ARM_ORDER | lived/null/shuffle tuple | run_protocol_c_prime.py:174-177 | pair loop/train branch | evet |
| TERMINATION_ENERGY | 0.05 | graph.py:122 | should_continue | evet |
| MAX_EVENTS | 20 | graph.py:127 | should_continue; multigen override | evet |
| MODEL_NAME | "llama-3.1-8b-instant" | graph.py:130 | _build_llm | evet |
| MAX_TOKENS | 150 | graph.py:132 | _build_llm | evet |
| MEMORY_ENABLED | True | graph.py:133 | retrieve/write kapıları | evet |
| EXPECTED_OUTCOME_MEMORY_PREFIX/MAX_CHARS/K | prefix/200/3 | graph.py:136-138 | memory expected | evet |
| EXPECTED_SOURCE_FALLBACK/MEMORY / PAYLOAD_KEY | fallback/memory/expected_source | graph.py:139-141 | payload + PE log | evet |
| MEMORY_OUTCOME_KEYS | actual_outcome/decision/outcome | graph.py:142 | entry text extract | evet |
| DAERM_LOAD_DOMAINS / DEFAULT_TARGET / AXIS_COUNT | 3 domains / resource_load / 3.0 | graph.py:145-151 | PE apply | evet |
| EXPECTED_OUTCOME_BY_DOMAIN | domain şablonları | graph.py:163-178 | fallback expected | evet |
| DRIFT_WARNING_TEMPLATE | format str | graph.py:181-183 | prompt inject | evet |
| SYSTEM_PROMPT | uzun str | graph.py:242-250 | agent system | evet |
| NODE_* / POOL_STEP_EMPTY_EXTRACTION | node adları / 0.0 | graph.py:252-257 | build_graph / pool | evet |
| STRATEGIC_EXPECTATION_* / FRICTION_SOLO / DOMINANT_DOMAIN_TO_NPC | templates / 0.0 / map | graph.py:260-273 | social_pre/NPC | evet |
| DRIFT_BIAS_DOMAINS | 4 domain | graph.py:276-281 / lora_update.py:36-41 | max drift bias / loss weight | evet |
| LLM_BACKEND_ENV/DEFAULT / GROQ_API_KEY_ENV / ENV_FILE_NAME | env names | graph.py:287-294 | LLM resolve / .env | evet |
| CROSS_AXIS_SPILLOVER | 0.20 | constraints.py:31 | delta/graph PE spillover | hayır |
| MAGNITUDE_PEAK_WEIGHT | 0.70 | constraints.py:33 | delta.py magnitude | hayır |
| ALLOSTATIC_SETPOINT_MAX | 0.75 | constraints.py:30 | state.py setpoints | hayır |
| PRECISION_HISTORY_WINDOW | 10 | constraints.py:66 | pe_history trim | hayır |
| PRECISION_EPSILON/MAX/MIN_HISTORY/MIN_WEIGHT/VAR_REF | 1e-6/1.2/2/0.5/1/12 | constraints.py:65-73 | semantic_similarity | hayır |
| NLI_CONTRADICTION_THRESHOLD / NLI_MODEL_NAME | 0.60 / deberta-v3-small | constraints.py:36-37 | nli_filter | hayır |
| ADAPTER_BASE_DIR / ADAPTER_SWITCH_MAX_MS | dau_runs/adapters / 1 | constraints.py:43-44 | local_llm | hayır |
| DPO_BATCH_SIZE/BETA/EPOCHS/LR/MAX_GRAD_NORM/MAX_SEQUENCE_TOKENS | 1/0.10/1/5e-5/1.0/256 | constraints.py:49-57 | local_llm DPO | hayır |
| PER_AGENT_LORA_ALPHA / RANK | 16 / 8 | constraints.py:41-42 | local_llm | hayır |
| PPR_WEIGHT_IN_SCORE / PPR_ALPHA / PPR_TOP_K_DOMAINS | 0.30 / 0.85 / 10 | constraints.py:60-62 | retrieval / ppr | hayır |
| DEFAULT_TIME_PRESSURE…GENERATION_END | build_default_constraints defaults | constraints.py:16-20 | _initial_state niche overwrite | hayır |
| METABOLIC_FLOOR | 0.05 | constraints.py:32 | graph import; enerji path kullanımı BELİRSİZ | hayır |
| METRIC_MIN/MAX / DEFAULT_ENERGY / DEFAULT_*_LOAD | 0.0/1.0 / 1.0 / 0.0 | state.py:21-27 | InternalState | evet |
| DELTA_THRESHOLD_NOISE/NORMAL/DEEP | 0.1/0.4/0.7 | delta.py:24-26 | classify; meta | evet |
| DRIFT_BIAS_ABSENT / HEAL_THRESHOLD / HEAL_RATE / TRAUMA_DECAY_BASE / HEALED_MAGNITUDE | 0.0/0.6/0.3/1.0/0.0 | drift.py:20-26 | drift/heal | evet |
| MARKER_* / INHERITED_SOMATIC_MARKERS / DEFAULT_INHERITED_SOMATIC_SCALE / LOSS_* | keys/tuple/0.0/1.0\|0.0 | emotional_weight.py:21-42 | EW + transfer | evet |
| T_COGNITIVE_ESCALATE/DEESCALATE / T_COOLDOWN_STEPS / W_* / NPC_* | 0.65/0.25/5/weights/actions | lod.py:22-41 | LOD/NPC | evet |
| SOCIAL_W1/W2 / TRUST_* / ENTROPY_WINDOW / MARKOV_WINDOW / ENTROPY_EMPTY | 0.5/0.5 / trust / 10 / 20 / 0.0 | social.py:22-46 | social load | evet |
| INITIAL_EVENT_COUNTER | 0 | time_model.py:19 | EventClock | evet |
| MAX_RETRIEVED_MEMORIES / MEMORY_STORE_PATH / CHROMA_PATH | 3 / dau_memory.db / dau_memory_chroma | memory_bridge.py:25-27 | retrieve default / init paths | evet |
| SEMANTIC_MODEL_NAME / EMPTY_PAIR_SIMILARITY / MISSING_TEXT_SIMILARITY | MiniLM / 1.0 / 0.0 | semantic_similarity.py:21-24 | PE sensor | evet |
| LORA_ENABLED_DEFAULT / LORA_TRUTHY / COMPLETION_FALLBACK / PE_RANK_MIN_GAP / NLI_FILTER_STATS | "0" / frozenset / continue / 1e-6 / zeros | lora_update.py:30-75 | train/pairs | evet |
| PROMPT_TEMPLATE / PREF_LIVED_CONTEXT_TEMPLATE / LOSS_WEIGHT_* | format strings / floats | lora_update.py:43-65 | pair prompts / loss | evet |
| FITNESS_W_* / FITNESS_*_THRESHOLD / WARNING_SOMATIC_SCALE / W_TRANSFER_VALENCE_BASE | 0.4/0.3/0.3 / 0.35/0.70 / 0.3 / 1.0 | fitness.py:20-36 | fitness/transfer | evet |
| POOL_MAX / POOL_REGEN_RATE / POOL_INIT / COLLAPSE_EPSILON / POOL_CRISIS_THRESHOLD / CRISIS_* | 100/0.15/80/0.05/0.30/2.5/0.4 | environment.py:19-30 | pool/crisis | evet |
| EXTRACTION_* / DECISION_TO_OUTCOME / KEYWORDS / PARSE_MAX / PERCENT_TO_POOL_SCALE | miktarlar/maps/tuples/25/100 | extraction.py:29-80 | decision→outcome/extraction | evet |
| GENERATION_TRANSFER_THRESHOLD / GENERATION_MIN_RECALL / DRIFT_TRANSFER_MIN / INHERITED_WARNING_KEY / SOMATIC_SCALE_KEY / APPLY_BIRTH_COUNTER | 0.6/1/1.5/keys/0 | generation.py:35-51 | transfer/apply | evet |
| META_* thresholds / MIN_VARIANCE_SAMPLE_SIZE / DEFAULT_RETRIEVAL_DOMAIN | True/0.3/0.4/0.5/0.4/2/uncertainty | meta_observer.py:40-50 | meta actuators | evet |
| META_HISTORY_SIZE / EPSILON / M_RATIO_LOW_THRESHOLD | 10 / 1e-6 / 0.6 | self_model.py:29-32 | self_model/meta | evet |
| CHROMA_COLLECTION_NAME / CHROMA_DB_PATH / SQLITE_MEMORY_PATH / DOMAIN_EDGE_WINDOW / EMBEDDING_DIM / SEED_BIRTH_COUNTER_DEFAULT | dau_memory / paths / 10 / 32 / 0 | store.py:36-42 | MemoryStore | evet |
| W_RECENCY/IMPORTANCE/RELEVANCE / DOMAIN_SOFT_MATCH / _DEFAULT_PPR_DB_PATH | 0.21/0.28/0.21 / 0.5 / dau_runs/memory.db | retrieval.py:22-33 | memory_score | evet |
| S_UNIT / R_MIN / TRAUMA_S_BASE | 0.1 / 0.05 / 10 | decay.py:18-20 | strength/retention | evet |
| NLI_CONTRADICTION_INDEX | 0 | nli_filter.py:22 | softmax index | evet |
| LOCAL_MODEL_NAME + LoRA/DPO module constants + GENERATION_MAX_NEW_TOKENS | local Llama-3.1-8B + targets + 64 | local_llm.py:38-54 | load/train/infer | evet |

## K4 — Varsayılan parametreler

| dosya:satır | imza | default | çağıran override? |
|---|---|---|---|
| run_cprime_multigen.py:194 | MockLLM.__init__(texts=…) | MOCK_DECISION_TEXTS | hayır — MockLLM() |
| run_cprime_multigen.py:245-253 | run_life_keep_vault(..., initial=None, energy_floor=AB_ENERGY_FLOOR) | None, 0.15 | initial=heir gen2'de; energy_floor override yok |
| run_cprime_multigen.py:571-578 | run_multigen_pair(*, events_*=…, k_gen2=…, pe_window_gen2=…) | module env ints | evet — run_cprime_multigen/CLI |
| run_cprime_multigen.py:601-610 | run_cprime_multigen(*, …, mock_llm=None) | env defaults; None→mock_llm_enabled() | evet — CLI; --mock-llm → True |
| run_cprime_multigen.py:667-677 | write_multigen_results_json(..., path=None, …) | path→RESULTS_PATH | evet — CLI --results |
| run_cprime_multigen.py:736-751 | argparse defaults | module constants | CLI override mümkün |
| run_protocol_c_prime.py:265 | _window_mean(pe_list, window=PE_WINDOW_EVENTS) | 10 | gen1 hayır; gen2 window=pe_window |
| run_protocol_c_prime.py:684-688 | _train_adapter(..., shuffled=False) | False | shuffled=(arm==ARM_SHUFFLE) |
| run_protocol_c_prime.py:ArmResult | gated=False, gate_reason='', n_unique=0, pe_gap_max=0.0, saturation_rate=EMPTY_MEAN, pi_*=EMPTY, pi_values=[] | multigen precision audit alanlarını set etmez → JSON default |
| graph.py:303 | load_env_file(env_path=None) | project .env | override yok |
| graph.py:524 | _recent_decision_outcomes(..., k=EXPECTED_OUTCOME_MEMORY_K) | 3 | iç çağrı aynı |
| graph.py:553-558 | retrieve_relevant(..., k=EXPECTED_OUTCOME_MEMORY_K) | explicit 3 | expected-memory path |
| graph.py:879-884 | retrieve_relevant(...) k yok | bridge default k=3 | agent_node override yok |
| graph.py:610-615 | _apply_prediction_error(..., drift_state=None, target_domain=None) | None | evaluator override eder |
| graph.py:1147 | build_graph(checkpointer=None) | None | multigen explicit None |
| meta_observer.py:227 | trigger_drift_healing(..., evaluator_healed_domains=None) | frozenset() | meta_observer_node override |
| generation.py:239-241 | consolidate_generation(..., f_agent=None, reward=0, threat=0) | legacy defaults | multigen f_agent+markers override |
| generation.py:309 | seed_fn(..., birth_counter=APPLY_BIRTH_COUNTER) | 0 | apply_generation sabit 0 |
| memory_bridge.py:68 | retrieve_relevant(..., k=MAX_RETRIEVED_MEMORIES) | 3 | çağırana bağlı |
| retrieval.py:91 | retrieve_top_k(..., k: int = 5) | 5 | memory_bridge k=3 geçirir → top_k'ya 3 gider |
| lora_update.py:358-361 | run_micro_train_preference_step(pairs=None, agent_id='default', model=None) | None/'default'/None | _train_adapter pairs+agent_id geçer |
| lora_update.py:174 | build_lived_trace_examples(..., pe_event_log=None) | [] if None | _build_lived_examples pe_rows geçer |
| store.py:127-131 | MemoryStore(chroma_path=…, sqlite_path=…, collection_name=…) | module defaults | multigen tmp paths override |
| store.py:258 | seed_inherited_record(..., birth_counter=0) | 0 | apply_generation APPLY_BIRTH_COUNTER |
| ppr_retrieval.py:83-84 | compute_ppr_scores(..., alpha=PPR_ALPHA, top_k=PPR_TOP_K_DOMAINS) | 0.85, 10 | çağıran default kullanır |
| fitness.py:50 | compute_fitness(..., pool_max=POOL_MAX) | 100.0 | self_model/caller |
| environment.py:121 | apply_crisis_trauma(..., base_magnitude=CRISIS_BASE_MAGNITUDE) | 0.4 | step_pool_with_crisis |
| local_llm.py:119 | load_local_model(agent_id='default') | "default" | local path |
| local_llm.py:675-679 | run_micro_train_preference_step(...) | pairs=None, agent_id=default | _train_adapter override |
| llm_backend.py:50 | LocalBackend.complete(..., agent_id='default') | "default" | graph agent_id geçer |

## K5 — Mevcut kontroller

| dosya:satır | kontrol | başarısız olursa |
|---|---|---|
| run_cprime_multigen.py:273 | assert start.agent_id == agent_id | AssertionError — life abort |
| run_cprime_multigen.py:351-352 | assert heir_blank.event_log/delta_log == [] | AssertionError — transfer abort |
| run_cprime_multigen.py:356-357 | assert heir.generation_record is record; agent_id | AssertionError |
| run_cprime_multigen.py:306-314 / :498-499 | gen2 diversity: n_unique < k_gen2 veya pe_gap_max < 1e-6 | gated=True + reason; life bitmiş; mean_pe saklanır; summary gated'i dışlar |
| run_cprime_multigen.py:429-437 | gen1 diversity _diversity_gate_reason | gated=True; train skip; print; phase-2 devam; delta_pe=NAN_DELTA |
| run_cprime_multigen.py:233 | unexpected stream type | TypeError |
| run_protocol_c_prime.py:183-190 | import assert AB_ENERGY_FLOOR / niche vs crisis | assert — process abort |
| run_protocol_c_prime.py:391-403 | n_unique < 5 veya pe_gap_max < 1e-6 | non-empty reason (caller gated) |
| run_protocol_c_prime.py:555-560 | len(pe_list) < n_events * 0.5 | WARN print only; pad+continue |
| run_protocol_c_prime.py:697-704 | LORA env truthy değil | silent (0,0) |
| run_protocol_c_prime.py:750-757 | trained flag false | WARN + (0,0) |
| run_protocol_c_prime.py:406-415 | non-finite float in _json_sanitize | → None in JSON |
| graph.py:418-422 | GROQ_API_KEY boş | RuntimeError — stream durur (multigen'de catch yok) |
| graph.py:850 | should_run_llm(lod) false | NPC path; LLM yok |
| graph.py:915 | drift_bias > DRIFT_BIAS_ABSENT | false → drift warning yok |
| graph.py:1036-1037 | not trauma ve magnitude >= HEAL_THRESHOLD | heal_drift atlanır (false branch) |
| graph.py:1127-1132 | len(event_log) >= MAX_EVENTS veya energy <= TERMINATION_ENERGY | END vs social_pre |
| graph.py:1129 | effective_energy = max(energy, AB_ENERGY_FLOOR) | floor > TERMINATION iken energy ile erken END pratikte kapalı |
| meta_observer.py:187-194 | META_LOD_OVERRIDE_ENABLED ve deep+low m_ratio | false → lod değişmez; true → SYSTEM_2 |
| meta_observer.py:209-212 | variance <= 0.3 | prune yok |
| meta_observer.py:239-243 | flags + f_agent < 0.5 + reward > 0.4 | heal yok |
| meta_observer.py:281-284 | m_ratio < 0.6 ve delta >= NORMAL | supplement retrieval yok |
| generation.py:98-167 | score/recall/w_transfer/drift kapıları | aday elenir veya warning işaretlenir |
| state.py:166-170 | somatic marker range | ValueError |
| state.py:408-418 | retrieval_context/pe_history tip | TypeError |
| constraints.py:107-112 | unknown key / out of range update | ValueError |
| delta.py:119-138 | magnitude thresholds / should_persist / is_trauma | classification / bool |
| drift.py:49-102 | trauma/heal/flag kapıları | update/heal/bias no-op veya apply |
| lod.py:109-146 | escalate/deescalate/should_run_llm | mode değişimi / bool |
| environment.py:129-130 | pool_ratio >= POOL_CRISIS_THRESHOLD | crisis trauma yok |
| environment.py:96 | pool_next <= POOL_MAX * COLLAPSE_EPSILON | collapsed=True |
| lora_update.py:122-128 / 286-299 | is_lora_enabled / PE gap / NLI | skip train / drop pair |
| lora_update.py:344-353 | shuffle identity guard | force swap first pair |
| nli_filter.py:57 | skor ≥ NLI_CONTRADICTION_THRESHOLD | bool polarity |
| store.py:202-203 | not decision['persist'] | return "" |
| store.py:270-271 | payload/source_node None | return None |
| decay.py:48-49 / 60-61 | strength<=0 / trauma | retention 0.0 / should_forget False |
| ppr_retrieval.py:46-47 | networkx yok in loader | RuntimeError |
| local_llm.py:135-139 | transformers/torch yok | RuntimeError |
| local_llm.py:593-594 / 666-667 | not trainable / step_count==0 | RuntimeError |
| local_llm.py:688-722 | LoRA off / no model / no pairs / no tokenizer | skip dict (trained=False) |
| fitness.py:76-80 | F thresholds | label low/high/normal |
| extraction.py:94-116 | token/keyword/regex/default | outcome + extraction miktarı |

## K6 — Boş/sıfır ile çıktı üretebilen yollar

| zincir | boş/sıfır nerede | taşındığı yer | JSON alanı |
|---|---|---|---|
| PE log boş → _pad_pe_list → [0.0]*n → _window_mean → 0.0 | get_pe_event_log boş / stream PE yazmadı | run_life_keep_vault → ArmResult/Gen2Result | gen1.pe_before/pe_after; gen2.mean_pe; gen2.delta_pe |
| PE log kısa → pad last (+ WARN if <0.5*n) | stream erken bitti | _pad_pe_list | aynı PE alanları |
| lived_examples=[] (ImportError veya event yok) | _phase1_diversity → n_unique=0, pe_gap_max=0.0 | ArmResult/Gen2Result | gen1/gen2 n_unique, pe_gap_max; sık gated=true |
| completions hepsi fallback/continue | diversity skip | aynı | gate alanları |
| arm==null veya LORA off / train fail / pairs=[] | n_pairs_trained=0, n_pairs_rejected=0 | ArmResult | gen1.n_pairs_trained, gen1.n_pairs_rejected |
| gen1 diversity gated | delta_pe=nan → _json_sanitize → null | ArmResult | gen1.delta_pe |
| ArmResult precision defaults doldurulmaz | asdict(gen1) | lineage.gen1 | saturation_rate=0.0, pi_n_distinct=0, n_pe_events_audited=0, n_saturated=0, pi_values=[] |
| drift tipi yanlış → DriftState() | birth log | BirthDriftLog | transfer.birth_drift_flags/magnitudes |
| record.inherited_memories=[] | len=0, ids=[] | BirthDriftLog | transfer.n_transfer_candidates, inherited_memory_ids |
| markers absent → .get(...,0.0) | consolidate inputs | fitness/transfer | transfer.f_agent / n_transfer_* dolaylı |
| gen2 gated=True | summary append skip | _summary | mean_gen2_pe_by_gen1_arm[arm] boş listede EMPTY_MEAN=0.0; n_usable_gen2_*=0 |
| expected memory fail → [] → fallback template | resolve_expected_outcome | event expected_source=fallback → PE | dolaylı gen*.mean_pe / pe_before/after |
| precision except → weight=1.0, pe=raw_pe | evaluator | _record_pe_event → pe_list | mean_pe (PE_w=raw) |
| empty decision → actual_outcome="" | MiniLM one-empty → sim=0 → PE=1.0 | pe_list | mean_pe |
| evaluator event_log boş → {} | PE yazılmaz | kısa/pad pe_list | PE alanları 0 pad |
| seed_inherited new_id None | id_map skip; context parent_id | heir retrieval_context | transfer.n_retrieval_context; vault kopyası olmayabilir |
| f_agent birth: t_survived=0 → denom=1 | build_self_model | BirthDriftLog | transfer.f_agent, fitness_class |
| gen2 event1 delta_log boş → apply_inherited_somatic_scale çağrılmaz | agent_node koşulu (delta_log non-empty) | ilk prompt scale yok | notes.somatic_scale; PE e1 bu kanaldan etkilenmez |
| PPR fail → ppr=0.0 | compute_memory_score | retrieve ranking | retrieval_context → dolaylı PE/transfer |
| PPR empty graph → {seed:1.0} | ppr_score_for_domain | score formülü | aynı |
| NLI off → tüm çiftler geçer (True) | build_pe_ranked_pairs | pairs → train | gen1.n_pairs_*; adapter disk |
| NLI_FILTER_STATS zeros start | _train_adapter delta | n_pairs_trained/rejected | gen1.n_pairs_* |
| social empty interactions → entropy 0.0 | social_pre/evaluator | T_cog / social_load | dolaylı LOD/PE |
| store persist false → return "" | record_delta | vault boş kalabilir | n_transfer_candidates=0 zinciri |
| local_llm train skip dict'leri | trained=False reasons | _train_adapter (0,0) | gen1.n_pairs_trained=0 |

## K7 — Rastgelelik ve determinizm

| dosya:satır | ne | seed/değer |
|---|---|---|
| run_protocol_c_prime.py:456-460 | _lock_seeds(seed) | random.seed; np.random.seed; _lock_torch_seed; DAU_LLM_SEED=str(seed); DAU_LLM_TEMPERATURE=str(TEMPERATURE) |
| run_cprime_multigen.py:411,446 | _lock_seeds call sites | gen1 phase-1 ve phase-2 başlangıcı |
| run_cprime_multigen.py — gen2 | _lock_seeds yok | run_gen2_measure öncesi seed lock çağrısı yok; process RNG gen1 sonrası durumda |
| run_protocol_c_prime.py:435-450 | torch lock | manual_seed; cuda.manual_seed_all if CUDA; threads; cudnn det; use_deterministic_algorithms(True, warn_only=…) |
| run_protocol_c_prime.py:470-478 | niche RNG | private random.Random(seed) — global RNG'den bağımsız |
| run_cprime_multigen.py:198-201 | MockLLM | calls % len(texts) — ayrı seed yok; döngüsel deterministik |
| run_protocol_c_prime.py:567-573 | _seed_from_agent_id | trailing int bekler; id `…-g1` → ValueError → hash(agent_id); hash PYTHONHASHSEED'e bağlı |
| lora_update.py:328-331 | shuffle_preference_pairs | random.Random(seed); rng.random()<0.5 swap |
| graph.py:395-401 | Groq seed opsiyonel | DAU_LLM_SEED int; yoksa seed yok |
| graph.py:386-392 | temperature | env veya 0.2 |
| graph.py:857,945 | EventClock(counter=len(event_log)) | event ordinal; wall-clock yok |
| store.py:59-65 | DeterministicHashEmbedding | sha256(text) → EMBEDDING_DIM floats |
| store.py:205,273 | uuid4() | yeni record id — koşumdan koşuma değişir |
| state.py:262 | Event.event_id uuid4 | event id non-deterministic |
| local_llm.py:62-75,410-428 | local sampling | env; do_sample iken sha256(seed:prompt)→step_seed; torch.manual_seed + cuda.manual_seed_all |
| local_llm.py:196-216 | _reset_active_adapter | reset_lora_parameters(init_lora_weights=True) — torch RNG LoRA-A |
| nli_filter.py:46-48 | NLI eval | torch.no_grad + softmax; seed yok |
| ppr_retrieval.py:98-103 | nx.pagerank | NetworkX/SciPy sayısal; seed argümanı yok |
| time.perf_counter / tempfile | wall / path entropy | wall_seconds; tmp dizin adları |

## K8 — Dış bağımlılık yüzeyi

| dosya:satır | yüzey | başarısız olursa |
|---|---|---|
| run_cprime_multigen.py:237-241 | tempfile.TemporaryDirectory + MemoryStore(chroma,sqlite) | constructor exception propagate (catch yok) |
| run_cprime_multigen.py:260 | graph_mod.load_env_file() | missing .env → return; read errors propagate |
| run_cprime_multigen.py:276-282 | build_graph + app.stream | LLM/network/graph errors propagate (agent_node wrap yok) |
| run_cprime_multigen.py:209-216 | mock patch _build_llm | restore finally |
| run_cprime_multigen.py:340-355 | consolidate/apply/build_self_model/store | exceptions propagate |
| run_cprime_multigen.py:559-568 | store.close / tmp.cleanup | swallowed — K1 çapraz |
| run_cprime_multigen.py:681,727 | mkdir + write_text JSON | OSError/JSON propagate |
| run_protocol_c_prime.py:706-724 | import lora_update / build_pe_ranked_pairs | ImportError/(0,0); Exception→(0,0) log yok — K1 |
| run_protocol_c_prime.py:740-748 | DPO train | except → WARN+(0,0) — K1 |
| graph.py:310-313 | disk .env read | yoksa no-op |
| graph.py:428-434,938 | Groq ChatGroq.invoke network | exception yukarı (multigen abort) |
| graph.py:417-422 | API key | RuntimeError |
| graph.py:928-935 | LocalBackend.complete + adapter disk | bu dosyada catch yok |
| graph.py:553-561 | retrieve_relevant (expected) | [] silent — K1 |
| graph.py:879-884 | retrieve_relevant (agent prompt) | catch yok — exception propagate |
| graph.py:604-607 | MiniLM semantic_prediction_error | encode/load fail → evaluator crash; load local_files sonra download |
| graph.py:1065-1068 | record_delta → store write | persist false skip; write hata propagate |
| meta_observer.py:291-296 | bound store retrieve | store None no-op; aksi hata propagate |
| generation.py:199-224,306-312 | list_nodes / payload / seed_inherited disk | payload None reconstruct; seed None map skip; diğer hata propagate |
| semantic_similarity.py:43-72 | SentenceTransformer HF | cache miss → network; fail → PE path crash veya K1 retry |
| memory_bridge.py:38-41 | MemoryStore default paths | multigen tmp ile override; initialize_memory path'i multigen kullanmaz |
| store.py:133-318 | Chroma PersistentClient + SQLite | I/O fail propagate (delete except pass — K1) |
| retrieval.py:70-74 | SQLite PPR ayrı connect | except → ppr=0.0 — K1 |
| ppr_retrieval.py:50-63 | sqlite3.connect + JOIN | fail → pagerank except fallback — K1 |
| nli_filter.py:29-34 | HF NLI from_pretrained | ağ/cache; fail → build_pe_ranked_pairs except → (0,0) — K1 |
| local_llm.py:78-158,231-280,427 | adapter disk + model load + CUDA + save | çeşitli skip/warning/RuntimeError — K1/K5 |
| llm_backend.py:34-62 | Groq invoke veya local generate | exception caller'a |

## BELİRSİZ

1. BELİRSİZ: Gen2 öncesi `_lock_seeds` yok — MiniLM/NLI/torch global RNG'nin gen2'de nasıl etkilendiği bu denetimde ölçülmedi.
2. BELİRSİZ: `_seed_from_agent_id`: agent_id `cprime-{arm}-{seed}-g1` trailing segment `g1` → ValueError → `hash(agent_id)`. Intentional olup olmadığı satırda yazılı değil; PYTHONHASHSEED sabit değilse süreçler arası seed değişir.
3. BELİRSİZ: `agent_node` retrieve (prompt) catch yok; `_past_outcomes_from_memory` catch var — Chroma kısmi fail senaryosu asimetrik.
4. BELİRSİZ: Geçersiz `DAU_LLM_TEMPERATURE` / `DAU_LLM_SEED` string: graph.py'de float/int catch yok — ValueError davranışı burada tanımlı değil.
5. BELİRSİZ: `LocalBackend.complete` / adapter path fail contract graph.py'de yok — local_llm içine bağlı.
6. BELİRSİZ: `seed_inherited_record` uuid4 heir id'leri — aynı vault replay'de id'ler koşumdan koşuma değişir; PE'ye dolaylı etki bu denetimde ölçülmedi.
7. BELİRSİZ: `ENERGY_DECAY_PER_EVENT` / `RESOURCE_LOAD_INCREMENT` / `SOCIAL_LOAD_INCREMENT` graph.py'de tanımlı; mevcut evaluator PE-DAERM path'inde referans görülmedi — dead veya başka path BELİRSİZ.
8. BELİRSİZ: Multigen stream'de `npc_decision`/SYSTEM_1: initial LOD SYSTEM_2; de-escalation sonrası reachable — her event garantisi yok.
9. BELİRSİZ: `ppr_retrieval`: multigen consolidation çağırmıyor; edge tablosu boş kalırsa sürekli empty-graph fallback — edge yazan başka yol var mı store.write_edge çağrı zincirinde doğrulanmalı.
10. BELİRSİZ: `DOMAIN_EDGE_WINDOW` (store.py:39) tanımlı; bu dosyada edge yazımına bağlayan kullanım görülmedi.
11. BELİRSİZ: `_DEFAULT_PPR_DB_PATH`=`dau_runs/memory.db` vs MemoryStore default `dau_memory.db` — getattr(_sqlite_path) varken tmp path kullanılır; getattr fail senaryosu BELİRSİZ.
12. BELİRSİZ: `constraints.DAU_NLI_FILTER_ENABLED` bool vs nli_filter env string — nli_filter constraints sembolünü import etmez.
13. BELİRSİZ: `METABOLIC_FLOOR` constraints'te; enerji formülünde fiili kullanım satırı bu turda satır-satır kilitlenmedi.
14. BELİRSİZ: `NLI_FILTER_STATS` process-global mutable dict — sequential arm loop; process-global yan etki.
15. BELİRSİZ: `ArmResult` precision alanları (saturation_rate, pi_*) multigen'de doldurulmuyor — JSON'a default sıfır/boş gidiyor; bilinçli mi belirsiz.
16. BELİRSİZ: Protocol C′ modül-level `DAU_CPRIME_*` env okumaları import'ta çalışır ama multigen helpers onları tüketmez — import-time assert'ler çalışır.
17. BELİRSİZ: BitsAndBytes fallback (local_llm.py:153-156): hangi Exception tetikler (import/config/runtime) satırda ayrılmamış.
18. BELİRSİZ: `disable_adapter` context manager (local_llm.py:182-185): Callable ise no-op return — adapter gerçekten disable olur mu bu yolda belirsiz.
19. BELİRSİZ: `personalization=None` pagerank (seed grafikte yok): NX default personalization semantiği burada belgelenmemiş.
20. BELİRSİZ: Stream value tipi: `_state_from_stream` DAUAgentState veya dict+model_validate — LangGraph sürümüne bağlı hangisinin geldiği.
21. BELİRSİZ: Crisis trauma: `step_pool_with_crisis` her pool_step'te wired; magnitude'un ateşlenmesi pool_ratio'ya bağlı — belirli seed'de ateşlenip ateşlenmediği koşuma bağlı.
22. BELİRSİZ: Chroma telemetry kapalı; HF from_pretrained ağ/cache ayrı kanal.
23. BELİRSİZ: `LIVED_TRACES_FILE_NAME` / `PREF_TRACES_FILE_NAME` / `ADAPTER_META_FILE_NAME` / `SIGNAL_V*` lora_update.py'de tanımlı; dosya gövdesinde write/open yok.
24. BELİRSİZ: `fitness.WARNING_SOMATIC_SCALE` generation.py tarafından kullanılır; fitness.py fonksiyon gövdesinde kullanılmaz.
25. BELİRSİZ: `time_model` → `build_default_constraints` yalnızca `__main__` altında (time_model.py:93-94) — multigen path'te değil.
26. BELİRSİZ: local_llm import at graph load: başarı ≠ çağrı; çağrı yalnızca backend=local ve/veya LoRA train.
27. BELİRSİZ: apply_inherited_somatic_scale: fonksiyon delta_log non-empty iken çağrılır; inherited scale marker'ların transfer'de context'e konup konmadığı koşuma bağlı.
28. BELİRSİZ: trigger_retrieval / trigger_drift_healing / lod_override / context_prune: meta_observer_node her zaman girer; iç gövde eşiklere bağlı no-op olabilir.

---

## Sayaç (üretim meta)

- Kapsanan dosya: 28
- K1 satır: 98
- K2 get satır: 24; K2 set satır: 7; K2 toplam: 31
- K3 satır: 91
- K4 satır: 30
- K5 satır: 43
- K6 satır: 25
- K7 satır: 19
- K8 satır: 27
- BELİRSİZ madde: 28
