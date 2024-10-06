python3 -m src.run_eval_v2 \
  --providers-path providers.json \
  --settings-path settings_v2.json \
  --output-path results/test.json \
  --player-name gpt-4o-mini \
  --interrogator-name gpt-4o-mini \
  --judge-name gpt-4o \
  --language en



python3 -m src.run_eval_crm \
  --providers-path providers.json \
  --settings-path settings_crm.json \
  --output-path results/crm_test_8.json \
  --player-name dolphin \
  --interrogator-name mixtral \
  --judge-name gpt-4o \
  --language en