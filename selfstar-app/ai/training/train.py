# -*- coding: utf-8 -*-
import os, mlflow
from trl import SFTTrainer, SFTConfig

from .config import (
    OUTPUT_DIR, TRAIN_PATH, VAL_PATH, MAX_SEQ_LEN, EPOCHS, TRAIN_BS, EVAL_BS,
    GRAD_ACCUM, LR, WARMUP, LOG_STEPS, SAVE_STEPS, EVAL_STEPS,
    RUN_NAME, BASE_MODEL, MLFLOW_TRACKING_URI,
    PUSH_TO_HUB, HF_REPO_ID, HF_REPO_PRIVATE, MERGE_AND_SAVE, MAKE_ZIP,
    PROJECT_ROOT
)
from .auth_hf import hf_login
from .modeling import load_tokenizer, load_base_model_4bit, apply_lora
from .data import build_dataset
from .mlflow_utils import init_mlflow, MLflowLoggingCallback
from .hub_utils import zip_dir, merge_lora_to_fp16, push_folder_to_hub

def main():
    # 1) 로그인
    hf_token = hf_login()

    # 2) 데이터
    tokenizer = load_tokenizer(hf_token)
    train_ds, val_ds = build_dataset(tokenizer)
    print(f"🧾 학습 샘플: {len(train_ds)} / 검증 샘플: {len(val_ds) if val_ds is not None else 0}")

    # 3) 모델 로드 + LoRA
    base = load_base_model_4bit(hf_token)
    model = apply_lora(base)

    # 4) MLflow
    init_mlflow()
    with mlflow.start_run(run_name=RUN_NAME):
        mlflow.log_params({
            "base_model": BASE_MODEL, "epochs": EPOCHS, "train_bs": TRAIN_BS, "eval_bs": EVAL_BS,
            "grad_accum": GRAD_ACCUM, "lr": LR, "warmup": WARMUP, "max_seq_len": MAX_SEQ_LEN,
            "train_path": TRAIN_PATH, "val_path": VAL_PATH, "output_dir": OUTPUT_DIR,
            "tracking_uri": MLFLOW_TRACKING_URI,
            "push_to_hub": PUSH_TO_HUB, "merge_and_save": MERGE_AND_SAVE, "make_zip": MAKE_ZIP
        })

        # 5) Trainer
        sft_args = SFTConfig(
            output_dir=OUTPUT_DIR,
            num_train_epochs=EPOCHS,
            per_device_train_batch_size=TRAIN_BS,
            per_device_eval_batch_size=EVAL_BS,
            gradient_accumulation_steps=GRAD_ACCUM,
            learning_rate=LR,
            lr_scheduler_type="cosine",
            warmup_ratio=WARMUP,
            logging_steps=LOG_STEPS,
            save_steps=SAVE_STEPS,
            eval_steps=EVAL_STEPS,
            evaluation_strategy="steps" if val_ds is not None else "no",
            gradient_checkpointing=True,
            bf16=True,
            max_seq_length=MAX_SEQ_LEN,
            packing=True,
            dataset_text_field="text",
            save_total_limit=2,
            optim="paged_adamw_8bit",
            do_eval=(val_ds is not None),
            report_to="none",
        )

        trainer = SFTTrainer(
            model=model, tokenizer=tokenizer,
            train_dataset=train_ds, eval_dataset=val_ds,
            args=sft_args, callbacks=[MLflowLoggingCallback()],
        )

        print("학습 시작")
        trainer.train()
        print("학습 종료")

        # 6) 저장 + MLflow 아티팩트
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        trainer.model.save_pretrained(OUTPUT_DIR)
        tokenizer.save_pretrained(OUTPUT_DIR)
        mlflow.log_artifacts(OUTPUT_DIR, artifact_path="comment_lora_artifacts")
        print("LoRA 어댑터 저장:", OUTPUT_DIR)

        # 7) (옵션) 병합 가중치 저장
        if MERGE_AND_SAVE:
            merged_dir = os.path.join(OUTPUT_DIR, "merged-fp16")
            merge_lora_to_fp16(BASE_MODEL, OUTPUT_DIR, merged_dir, hf_token)
            mlflow.log_artifacts(merged_dir, artifact_path="merged_fp16")
            print("병합 가중치 저장:", merged_dir)

        # 8) (옵션) zip 묶기 (드라이브에서 바로 다운로드 가능)
        if MAKE_ZIP:
            zip_path = os.path.join(PROJECT_ROOT, "ai", "training", "outputs", "comment_lora.zip")
            zip_dir(OUTPUT_DIR, zip_path)
            mlflow.log_artifact(zip_path, artifact_path="zips")
            print("ZIP 생성:", zip_path)

        # 9) (옵션) HF Hub 업로드
        if PUSH_TO_HUB:
            url = push_folder_to_hub(HF_REPO_ID, OUTPUT_DIR, HF_REPO_PRIVATE, hf_token)
            print("Hugging Face Hub 업로드 완료:", url)

        print("모든 후처리 완료")

if __name__ == "__main__":
    main()
