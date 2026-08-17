# dau_runs — ham ölçüm etiketleri

> Bu tablo `dau_runs/` altındaki ham ölçüm çıktılarını etiketler.
> **`ESKİ ALET` işaretli dosyalar silinmemeli** — tarihçe ve alet evriminin
> kanıtı. Ama bugünkü sayılarla **karşılaştırılamazlar** (D-036/D-037/D-042).

⚠ **`Tarih` sütunu dosyanın mtime'ıdır ve gerçek koşum tarihi değildir.**
`dau_runs/` **git'te takip edilmiyor** (`.gitignore:7`, takipli dosya sayısı
sıfır), yani tarihi doğrulayacak bir commit kaydı yok. Dosyaya sonradan
dokunulduysa mtime kayar — ölçülmüş örnek: `overnight_audit_results.json`
mtime'ı 08-12 gösteriyor ama içeriği Protocol C dönemine ait. **Durum
sütunu içeriğe göre verildi, tarihe göre değil.**

## Durum kategorileri

| Durum | Anlamı |
|---|---|
| **GEÇERLİ** | Ön-kayıtlı doğrulayıcı koşum ve analizi. Nihai sonuç bunlardan okunur |
| **REGRESYON** | Alet doğrulaması; güncel aletle koşuldu, hipotez testi değil. Kullanılabilir |
| **KEŞİFSEL** | Güncel aletle (D-042 sonrası) koşulan **keşifsel** ölçüm. Sonuç iddiası taşımaz ama sayıları bugünkü aletten |
| **ESKİ ALET** | D-036 / D-037 / D-042 öncesi. Bugünkü sayılarla karşılaştırılamaz |

| Dosya | Tarih | Durum | Not |
|---|---|---|---|
| b3_prereg_analysis.json | 2026-08-12 12:31 | GEÇERLİ | B3 ön-kayıt analizi |
| baseline_d037_n3_local.json | 2026-08-11 02:07 | REGRESYON | D-037; N=3; local |
| control_d042_n3_local.json | 2026-08-11 13:04 | REGRESYON | D-042; N=3; local |
| cprime_diversity_prereg_scan.json | 2026-08-07 19:34 | ESKİ ALET | C′ diversity ön-kayıt taraması |
| dry_run_preflight.json | 2026-08-08 02:38 | ESKİ ALET | preflight dry-run |
| dry_run_preflight_heartbeat.json | 2026-08-08 02:38 | ESKİ ALET | preflight dry-run heartbeat |
| exploratory_a6_precision_and_channel_audit.json | 2026-08-11 18:42 | KEŞİFSEL | A6 / **D-050** — precision + kanal denetimi. Güncel alet, keşifsel |
| exploratory_gen2_endpoint_sensitivity.json | 2026-08-11 13:50 | KEŞİFSEL | A5 / **D-045** — gen2 uç nokta duyarlılığı. Güncel alet, keşifsel |
| exploratory_greedy_vs_sampled_50events.json | 2026-08-10 03:55 | ESKİ ALET | greedy vs sampled; 50 olay; exploratory |
| exploratory_pair_design_replay.json | 2026-08-10 14:07 | ESKİ ALET | çift tasarımı replay; exploratory |
| exploratory_train_determinism.json | 2026-08-10 22:56 | ESKİ ALET | eğitim determinizmi; exploratory |
| graph-run-74aa4170.json | 2026-08-01 05:11 | ESKİ ALET | **ölçüm değil** — LangGraph koşum state dökümü (`agent_id`/`db_path`/`thread_id`/`state`) |
| lr_probe_pairs.json | 2026-08-10 13:09 | ESKİ ALET | lr probe çiftleri |
| lr_probe_results.json | 2026-08-10 13:13 | ESKİ ALET | lr probe sonuçları |
| nli_score_distribution.json | 2026-08-10 13:00 | ESKİ ALET | NLI skor dağılımı |
| overnight_audit_results.json | ⚠ mtime 08-12, **içerik çok daha eski** | ESKİ ALET | Protocol C / metacognition dönemi: `npc_baseline`, `meta_ab_*`, `nuance_loss_pilot`, `sensor_label`. Layer 5 çalışmasından |
| pilot_d033_n3_local.json | 2026-08-10 16:17 | ESKİ ALET | D-033 pilot; N=3; local |
| pilot_d066_metabolic_n2.json | 2026-08-13 14:56 | KEŞİFSEL | **D-068** — metabolik evrenin ilk pilotu (N=2, seed 4001–4002). ⚠ `run_quality=flagged`, uç nokta %71 padding ⇒ `pe_after` sayıları **okunmaz**. Fizik D-066/D-067 sonrası ⇒ önceki hiçbir dosyayla karşılaştırılamaz |
| prereg_b2_batch1_2004_2023.json | 2026-08-12 02:11 | GEÇERLİ | B2 batch1; seed 2004–2023 |
| prereg_b2_batch2_2024_2043.json | 2026-08-12 11:21 | GEÇERLİ | B2 batch2; seed 2024–2043 |
| protocol_c_prime_heartbeat.json | 2026-08-07 20:45 | ESKİ ALET | C′ heartbeat |
| protocol_c_prime_multigen_pilot_n3_local.json | 2026-08-09 09:19 | ESKİ ALET | C′ multigen pilot; N=3; local |
| protocol_c_prime_precision_smoke.json | 2026-08-08 02:45 | ESKİ ALET | C′ precision smoke |
| protocol_c_prime_precision_smoke_heartbeat.json | 2026-08-08 02:45 | ESKİ ALET | C′ precision smoke heartbeat |
| protocol_c_prime_precision_smoke_v3.json | 2026-08-08 03:00 | ESKİ ALET | C′ precision smoke v3 |
| protocol_c_prime_precision_smoke_v3_heartbeat.json | 2026-08-08 02:58 | ESKİ ALET | C′ precision smoke v3 heartbeat |
| protocol_c_prime_results.json | 2026-08-07 20:51 | ESKİ ALET | C′ results |
| protocol_c_prime_v2_smoke_results.json | 2026-08-06 22:38 | ESKİ ALET | C′ v2 smoke |
| repro_a_seed2001.json | 2026-08-10 23:30 | ESKİ ALET | repro a; seed 2001 |
| repro_b_seed2001.json | 2026-08-10 23:51 | ESKİ ALET | repro b; seed 2001 |
| repro_c_strict_seed2001.json | 2026-08-11 00:21 | ESKİ ALET | repro c strict; seed 2001 |
| repro_d038_n3_local.json | 2026-08-11 03:13 | REGRESYON | D-038; N=3; local |
| repro_d_strict_seed2001.json | 2026-08-11 00:42 | ESKİ ALET | repro d strict; seed 2001 |
| smoke_d032_local.json | 2026-08-10 14:51 | ESKİ ALET | D-032 smoke; local |
| step0_d035_n3_local.json | 2026-08-10 20:18 | ESKİ ALET | D-035 Adım 0; N=3; local |
| sweep_d092_texts.json | 2026-08-17 | KEŞİFSEL | **D-092 / 0a-2** — D-090 taramasının yeni eşlemeyle tekrarı (57 çağrı). ⭐ **Ham karar metinleri saklandı** (D-091'in ilan edilmiş sınırı buydu). D-kaydı bu dosyayı `scratchpad/sweep_d092.json` diye anar; içerik **aynı**, buraya kalıcılık için kopyalandı |
| validate_d092_n2.json | 2026-08-17 | KEŞİFSEL | **D-092 / 0a-3** — eşleme onarımından sonraki canlı doğrulama, N=2 (seed 5008–5009), `--lora`, `run_quality=flagged`. gen2 `defect` payı **%53.3** |
| sweep_dpo_hyperparams.json / .jsonl | 2026-08-12 | KEŞİFSEL | **D-058/D-059** — `lr` × kırpma taraması, 96 hücre. `.jsonl` devam ettirilebilirlik kaydı; seed bazında `dpo_loss` burada |
| training_artifacts/ (dizin, 8 dosya) | 2026-08-12 | KEŞİFSEL | **D-057** — eğitim girdilerinin diske dökümü (`DAU_DUMP_TRAINING_ARTIFACTS`), seed 3001–3004 × iki kol. D-059 ve **D-062**'nin korpusu |
| u3_model_diversity_Qwen__Qwen2.5-7B-Instruct.json | 2026-08-10 03:32 | ESKİ ALET | U3 model diversity; Qwen2.5-7B |
| u3_model_diversity_meta-llama__Meta-Llama-3.1-8B-Instruct.json | 2026-08-10 03:31 | ESKİ ALET | U3 model diversity; Llama-3.1-8B |
| vram_spike_results.json | 2026-08-06 19:17 | ESKİ ALET | VRAM spike |
| vram_train_peak_nf4.json | 2026-08-10 04:07 | ESKİ ALET | VRAM train peak; NF4 |
| w1_pe_loglik_confound.json | 2026-08-13 10:31 | KEŞİFSEL | W1 / **D-062** — taban model log-olabilirliği vs PE; 200 olay + 186 çift + seed bazında özet |
| w3_endpoint_resolution.json | 2026-08-13 | KEŞİFSEL | W3 / **D-064** — uç nokta çözünürlük envanteri (21 aday) + birincilin alan-alan dökümü. ⚠ **Etki içermez**, bilerek |
