# -*- coding: utf-8 -*-
# [올인원/ASCII 문자열만] 로컬 -> Colab 노트북 생성/업로드 -> Colab에서 학습 실행
# - 파이썬 소스 안 "문자열 리터럴"은 원칙적으로 ASCII만 사용 (윈도우 인코딩 문제 회피)
# - 단, "Colab 노트북 마크다운"은 한국어로 표시하기 위해 UTF-8 문자열을 사용 (파일 헤더로 안전)
# - 한국어 설명은 주석(#)으로 상세히 기재
#
# 사전 준비:
#   1) 이 파일을 ai/training/run_on_colab.py 로 저장
#   2) 같은 폴더에 OAuth 파일(client_secrets.json 또는 oauth_client.json) 배치
#   3) pip install PyDrive2 google-auth-oauthlib
#
# 사용(Windows PowerShell):
#   cd C:\Users\smhrd\Documents\GitHub\selfstar\ai\training
#   python run_on_colab.py --open
#
# 동작 개요:
#   - 프로젝트 폴더(ai)를 ZIP으로 묶음
#   - Google Drive(MyDrive/<ColabRuns>)에 ZIP 업로드
#   - 해당 ZIP을 풀고 학습/MLflow/간단 추론을 수행하는 Colab 노트북을 생성하여 업로드
#   - Colab 링크 출력 (옵션으로 브라우저 자동 오픈)
#
# 중요(Colab 환경):
#   - 첫 셀에서 GPU 런타임 여부를 확인하고, GPU가 아니면 한국어 안내와 함께 종료
#   - 하이퍼파라미터는 "3) 하이퍼파라미터/경로 설정" 셀에서 직접 수정
#   - 학습/MLflow 결과는 MyDrive/SelfStar/... 경로로 저장되도록 환경변수 설정

import os
import sys
import json
import zipfile
import pathlib
import argparse
import webbrowser
from datetime import datetime
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# 기본 경로 설정: 이 파일 기준으로 상위가 ai 폴더
DEFAULT_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]  # .../ai
DEFAULT_COLAB_DIR = "ColabRuns"  # Drive/MyDrive/ColabRuns
COLAB_NOTEBOOK_TITLE = "SELFSTAR_ALL_IN_ONE_ASCII"

# ---------------------------------
# 유틸: 사람이 보기 쉬운 파일 크기 문자열
# ---------------------------------
def human_size(num: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num < 1024.0:
            return f"{num:3.1f}{unit}"
        num /= 1024.0
    return f"{num:.1f}PB"

# ---------------------------------
# Colab 노트북 셀 헬퍼
#  - 코드 셀: src는 가급적 ASCII만 사용(셸 명령 등 호환성↑)
#  - 마크다운 셀: 한국어로 친절하게 안내(ensure_ascii=False로 저장)
# ---------------------------------
def nb_code_cell(src: str):
    """
    Colab/nbformat 표준의 code cell 생성.
    주의: src는 가급적 ASCII로 유지(윈도우/콜랩 간 인코딩 이슈 최소화).
    """
    return {
        "cell_type": "code",
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in src.splitlines()]
    }

def nb_md_cell(lines):
    """
    마크다운 셀 생성. 한국어 설명을 자연스럽게 표기.
    lines: 문자열 리스트(각 항목이 한 줄)
    """
    # nbformat은 문자열 리스트를 그대로 사용하므로 줄 끝 개행 포함 X
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in lines]
    }

# ---------------------------------
# Colab 노트북 본문 생성
#  - 한국어 마크다운으로 섹션/주의사항을 자세히 표기
#  - 코드 셀은 실행 안정성을 위해 ASCII 위주로 구성
# ---------------------------------
def build_notebook(project_zip_path: str, project_root_dirname: str):
    """
    로컬에서 업로드한 ZIP을 Colab에서 해제하고, GPU 체크/하이퍼파라미터/학습/추론까지
    실행할 수 있는 노트북을 JSON 문자열로 생성.
    """
    cells = []

    # 표지/개요(한국어 마크다운)
    cells.append(nb_md_cell([
        "# SelfStar.AI 코랩 학습 실행 노트북 (자동 생성)",
        "",
        "이 노트북은 로컬 스크립트로 자동 생성되었습니다.",
        "아래 순서대로 **위에서 아래로** 실행하세요.",
        "",
        "1) **GPU 런타임 점검**: GPU가 아니면 안내 후 종료합니다.",
        "2) **구글 드라이브 마운트**: MyDrive에 접근합니다.",
        "3) **업로드 ZIP 해제**: `/content`에 프로젝트를 풉니다.",
        "4) **하이퍼파라미터/경로 설정**: 필요한 값을 수정합니다.",
        "5) **필수 패키지 설치**: 학습에 필요한 패키지 설치.",
        "6) **학습 실행**: MLflow 로깅, 체크포인트/어댑터 저장.",
        "7) **간단 추론 테스트**: 학습된 어댑터로 샘플 생성.",
        "",
        "> ⚠️ **주의**: 런타임이 재시작되면 파일/환경이 초기화될 수 있으니, 필요 시 ZIP 복사/해제부터 다시 진행하세요."
    ]))

    # 0) GPU 체크 (한국어 마크다운 + 코드)
    cells.append(nb_md_cell([
        "## 0) GPU 런타임 점검",
        "- 현재 파이썬/작업경로를 출력하고, `nvidia-smi`로 GPU 연결 여부를 확인합니다.",
        "- GPU가 아니면 메뉴에서 **런타임 → 런타임 유형 변경 → 하드웨어 가속기: GPU**로 바꾼 뒤 **다시 이 셀을 실행**하세요."
    ]))
    cells.append(nb_code_cell(
        "# [0] GPU runtime check\n"
        "import os, sys, subprocess\n"
        "def sh(cmd):\n"
        "    return subprocess.run(cmd, shell=True, check=False)\n"
        "print('[INFO] Python:', sys.version)\n"
        "print('[INFO] CWD:', os.getcwd())\n"
        "print('[STEP] Checking GPU availability...')\n"
        "rc = sh('nvidia-smi').returncode\n"
        "if rc != 0:\n"
        "    print('[WARN] CPU runtime detected.')\n"
        "    print('Menu: Runtime -> Change runtime type -> Hardware accelerator: GPU -> Save')\n"
        "    print('Then re-run this cell.')\n"
        "    raise SystemExit(0)\n"
        "print('[OK] GPU runtime confirmed.')\n"
    ))

    # 1) 드라이브 마운트
    cells.append(nb_md_cell([
        "## 1) 구글 드라이브 마운트",
        "- MyDrive에 접근하기 위해 드라이브를 마운트합니다.",
        "- 권한 팝업이 뜨면 허용을 눌러주세요."
    ]))
    cells.append(nb_code_cell(
        "# [1] Mount Google Drive\n"
        "from google.colab import drive\n"
        "drive.mount('/content/drive', force_remount=True)\n"
        "print('[OK] Drive mounted at /content/drive')\n"
    ))

    # 2) 업로드된 ZIP 해제
    cells.append(nb_md_cell([
        "## 2) 업로드 ZIP 해제",
        f"- 업로드된 ZIP 경로: `{project_zip_path}`",
        f"- 해제 대상 디렉토리: `/content/{project_root_dirname}` (기존 존재 시 삭제 후 재생성)",
        "- 해제 후 작업 디렉토리를 해당 폴더로 변경합니다."
    ]))
    cells.append(nb_code_cell(
        "# [2] Unzip uploaded project\n"
        f"PROJECT_ZIP = r\"{project_zip_path}\"\n"
        f"PROJECT_DIRNAME = r\"{project_root_dirname}\"\n"
        "import os, zipfile, shutil\n"
        "from pathlib import Path\n"
        "BASE = Path('/content')\n"
        "if (BASE/PROJECT_DIRNAME).exists():\n"
        "    print('[INFO] Remove existing:', BASE/PROJECT_DIRNAME)\n"
        "    shutil.rmtree(BASE/PROJECT_DIRNAME)\n"
        "print('[STEP] Extracting zip:', PROJECT_ZIP)\n"
        "with zipfile.ZipFile(PROJECT_ZIP, 'r') as zf:\n"
        "    zf.extractall(BASE)\n"
        f"%cd /content/{project_root_dirname}\n"
        "print('[OK] Extracted and changed dir.')\n"
        "!pwd && ls -al\n"
    ))

    # 3) 하이퍼파라미터/경로
    cells.append(nb_md_cell([
        "## 3) 하이퍼파라미터 / 경로 설정 (여기서 수정)",
        "- 학습에 사용할 에폭, 러닝레이트, 배치 크기 등 기본값을 설정합니다.",
        "- MLflow를 로컬 경로(파일 모드)로 설정하며, 산출물/로그 저장 경로를 MyDrive 아래로 지정합니다.",
        "- (선택) Hugging Face 토큰을 `HUGGINGFACE_TOKEN` 환경변수로 전달할 수 있습니다."
    ]))
    cells.append(nb_code_cell(
        "# [3] Hyperparams and paths (edit here)\n"
        "from datetime import datetime\n"
        "STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')\n"
        "HUGGINGFACE_TOKEN = ''  # example: hf_xxx (or use userdata.get('HF_TOKEN'))\n"
        "EXPERIMENT_PREFIX = 'SelfStar'\n"
        "HP = dict(\n"
        "  epochs=1,\n"
        "  lr=2e-4,\n"
        "  train_bs=1,\n"
        "  eval_bs=1,\n"
        "  grad_accum=8,\n"
        "  max_seq_len=2048,\n"
        "  warmup=0.03,\n"
        "  log_steps=20,\n"
        "  save_steps=200,\n"
        "  eval_steps=200,\n"
        "  seed=42,\n"
        "  make_zip=1,\n"
        "  merge_and_save=0,\n"
        "  push_to_hub=0,\n"
        "  run_name=f'comment-lora_{STAMP}',\n"
        "  mlflow_experiment='selfstar-comment-lora',\n"
        "  output_dir='',\n"
        "  resume_from=None,\n"
        "  init_adapter_dir=None,\n"
        "  reset_optimizer_on_resume=True,\n"
        ")\n"
        "BASE_DRIVE = f\"/content/drive/MyDrive/{EXPERIMENT_PREFIX}\"\n"
        "MLFLOW_DIR = f\"{BASE_DRIVE}/mlruns\"\n"
        "OUTPUT_DIR = HP['output_dir'] or f\"{BASE_DRIVE}/outputs/{HP['run_name']}\"\n"
        "import os\n"
        "os.environ['MLFLOW_TRACKING_URI'] = f'file://{MLFLOW_DIR}'\n"
        "os.environ['OUTPUT_DIR'] = OUTPUT_DIR\n"
        "tok = HUGGINGFACE_TOKEN\n"
        "try:\n"
        "    from google.colab import userdata\n"
        "    tok = tok or userdata.get('HF_TOKEN')\n"
        "except Exception:\n"
        "    pass\n"
        "if tok:\n"
        "    os.environ['HUGGINGFACE_TOKEN'] = tok\n"
        "print('[OK] MLFLOW_TRACKING_URI =', os.environ['MLFLOW_TRACKING_URI'])\n"
        "print('[OK] OUTPUT_DIR =', os.environ['OUTPUT_DIR'])\n"
        "print('[OK] HP preview =', {k:HP[k] for k in sorted(HP)})\n"
        "print('[OK] HF token present:', bool(tok))\n"
    ))

    # 4) 패키지 설치
    cells.append(nb_md_cell([
        "## 4) 필수 패키지 설치",
        "- transformers / trl / peft / datasets / accelerate / bitsandbytes / mlflow 등을 설치합니다.",
        "- 설치 시간은 런타임/네트워크 상태에 따라 달라질 수 있습니다."
    ]))
    cells.append(nb_code_cell(
        "# [4] Install required packages\n"
        "!pip -q install -U mlflow transformers>=4.43 trl>=0.9.6 peft>=0.12.0 "
        "datasets>=2.20.0 accelerate bitsandbytes>=0.44.1 huggingface_hub\n"
        "print('[OK] pip install done')\n"
    ))

    # 5) 학습 코드(한 파일 내 정의)
    cells.append(nb_md_cell([
        "## 5) 학습 코드 정의",
        "- 데이터셋 로드, LoRA 어댑터 구성, `SFTTrainer` 학습 루프 등을 한 셀에 정의합니다.",
        "- MLflow 로깅, 체크포인트/어댑터 저장, 옵션 병합 저장까지 포함합니다."
    ]))
    cells.append(nb_code_cell(
        "# [5] Training code (single-file, ASCII only)\n"
        "import os, time\n"
        "from dataclasses import dataclass, asdict\n"
        "from pathlib import Path\n"
        "from typing import Optional\n"
        "import mlflow, torch\n"
        "from datasets import load_dataset\n"
        "from transformers import AutoTokenizer, AutoModelForCausalLM\n"
        "from trl import SFTTrainer, SFTConfig\n"
        "from peft import LoraConfig, get_peft_model, PeftModel\n"
        "HERE = Path('/content/ai/training')\n"
        "DATA_DIR = HERE / 'data'\n"
        "BASE_MODEL = os.getenv('BASE_MODEL', 'meta-llama/Meta-Llama-3.1-8B-Instruct')\n"
        "HF_TOKEN = os.getenv('HUGGINGFACE_TOKEN')\n"
        "@dataclass\n"
        "class HParams:\n"
        "    epochs:int=1; lr:float=2e-4; train_bs:int=1; eval_bs:int=1; grad_accum:int=8\n"
        "    max_seq_len:int=2048; warmup:float=0.03; log_steps:int=20; save_steps:int=200; eval_steps:int=200; seed:int=42\n"
        "    make_zip:int=1; merge_and_save:int=0; push_to_hub:int=0\n"
        "    run_name:str='comment-lora'; mlflow_experiment:str='selfstar-comment-lora'; output_dir:str=''\n"
        "    resume_from:Optional[str]=None; init_adapter_dir:Optional[str]=None; reset_optimizer_on_resume:bool=True\n"
        "    def to_dict(self):\n"
        "        d=asdict(self); d['lr']=float(self.lr); d['warmup']=float(self.warmup); return d\n"
        "def _prepare_out(hp):\n"
        "    if hp.output_dir: out=Path(hp.output_dir)\n"
        "    else: out=HERE/'outputs'/f\"{hp.run_name}_{time.strftime('%Y%m%d_%H%M%S')}\"\n"
        "    out.mkdir(parents=True, exist_ok=True); return out\n"
        "def _find_latest_ckpt(out:Path):\n"
        "    cks=sorted([p for p in out.glob('checkpoint-*') if p.is_dir()], key=lambda p:int(p.name.split('-')[-1]))\n"
        "    return cks[-1] if cks else None\n"
        "def _load_jsonl(train_path, val_path=None):\n"
        "    def pack(ds):\n"
        "        texts=[]\n"
        "        for ex in ds:\n"
        "            if 'text' in ex and ex['text']:\n"
        "                texts.append(str(ex['text']))\n"
        "            else:\n"
        "                u=str(ex.get('input','')).strip(); a=str(ex.get('output','')).strip()\n"
        "                if u or a: texts.append(f\"<|user|>\\n{u}\\n<|assistant|>\\n{a}\")\n"
        "        return {'text':texts}\n"
        "    d={}; tr=load_dataset('json', data_files=train_path, split='train')\n"
        "    d['train']=tr.map(pack, batched=True, remove_columns=tr.column_names)\n"
        "    if val_path and Path(val_path).exists():\n"
        "        va=load_dataset('json', data_files=val_path, split='train')\n"
        "        d['validation']=va.map(pack, batched=True, remove_columns=va.column_names)\n"
        "    return d\n"
        "def _build_model_and_tok(max_len, init_adapter_dir):\n"
        "    print('[STEP] Loading base model:', BASE_MODEL)\n"
        "    tok=AutoTokenizer.from_pretrained(BASE_MODEL, use_fast=True, token=HF_TOKEN, trust_remote_code=True)\n"
        "    if tok.pad_token is None: tok.pad_token=tok.eos_token\n"
        "    base=AutoModelForCausalLM.from_pretrained(\n"
        "        BASE_MODEL,\n"
        "        token=HF_TOKEN,\n"
        "        torch_dtype=(torch.bfloat16 if torch.cuda.is_available() else torch.float32),\n"
        "        device_map='auto', trust_remote_code=True\n"
        "    )\n"
        "    if init_adapter_dir:\n"
        "        print('[INFO] Warm-start from adapter:', init_adapter_dir)\n"
        "        model=PeftModel.from_pretrained(base, init_adapter_dir)\n"
        "    else:\n"
        "        l=LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,\n"
        "            target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'])\n"
        "        model=get_peft_model(base, l)\n"
        "    print('[OK] Model and tokenizer ready')\n"
        "    return model, tok\n"
        "def train_once(hp:HParams):\n"
        "    print('[STEP] Prepare output dir')\n"
        "    out=_prepare_out(hp)\n"
        "    train_path=os.getenv('TRAIN_PATH', str(DATA_DIR/'train.jsonl'))\n"
        "    val_path=os.getenv('VAL_PATH', str(DATA_DIR/'val.jsonl'))\n"
        "    print('[INFO] Train path =', train_path)\n"
        "    print('[INFO] Val path   =', val_path)\n"
        "    mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI', f'file://{HERE/'mlruns'}'))\n"
        "    mlflow.set_experiment(hp.mlflow_experiment)\n"
        "    print('[STEP] Loading dataset...')\n"
        "    ds=_load_jsonl(train_path, val_path if Path(val_path).exists() else None)\n"
        "    print('[OK] Dataset ready. Splits =', list(ds.keys()))\n"
        "    model,tok=_build_model_and_tok(hp.max_seq_len, hp.init_adapter_dir)\n"
        "    resume_arg=False\n"
        "    if hp.resume_from:\n"
        "        ck=_find_latest_ckpt(out) if hp.resume_from=='latest' else Path(hp.resume_from)\n"
        "        if ck and Path(ck).exists(): resume_arg=str(ck)\n"
        "        print('[INFO] Resume from checkpoint =', resume_arg)\n"
        "    cfg=SFTConfig(\n"
        "        output_dir=str(out), num_train_epochs=hp.epochs,\n"
        "        per_device_train_batch_size=hp.train_bs, per_device_eval_batch_size=hp.eval_bs,\n"
        "        gradient_accumulation_steps=hp.grad_accum, learning_rate=hp.lr, lr_scheduler_type='cosine', warmup_ratio=hp.warmup,\n"
        "        logging_steps=hp.log_steps, save_steps=hp.save_steps,\n"
        "        evaluation_strategy=('steps' if 'validation' in ds else 'no'), eval_steps=hp.eval_steps,\n"
        "        save_total_limit=2, bf16=torch.cuda.is_available(), seed=hp.seed,\n"
        "        max_seq_length=hp.max_seq_len, report_to=[], optim='paged_adamw_8bit'\n"
        "    )\n"
        "    trainer=SFTTrainer(model=model, tokenizer=tok, args=cfg,\n"
        "        train_dataset=ds['train'], eval_dataset=ds.get('validation'), dataset_text_field='text', packing=False)\n"
        "    print('[OK] Trainer initialized')\n"
        "    with mlflow.start_run(run_name=hp.run_name):\n"
        "        print('[STEP] MLflow run started:', hp.run_name)\n"
        "        mlflow.log_params(hp.to_dict()); mlflow.log_param('base_model', os.getenv('BASE_MODEL','meta-llama/Meta-Llama-3.1-8B-Instruct'))\n"
        "        mlflow.log_param('train_path', train_path)\n"
        "        if Path(val_path).exists(): mlflow.log_param('val_path', val_path)\n"
        "        if resume_arg: mlflow.log_param('resume_from_checkpoint', resume_arg)\n"
        "        if hp.init_adapter_dir: mlflow.log_param('init_adapter_dir', hp.init_adapter_dir)\n"
        "        if resume_arg and hp.reset_optimizer_on_resume:\n"
        "            trainer.create_optimizer_and_scheduler(num_training_steps=None)\n"
        "            print('[INFO] Optimizer/scheduler reset on resume')\n"
        "        print('[STEP] Start training...')\n"
        "        trainer.train(resume_from_checkpoint=resume_arg)\n"
        "        print('[OK] Training finished')\n"
        "        metrics=trainer.evaluate() if 'validation' in ds else {}\n"
        "        print('[INFO] Eval metrics =', metrics)\n"
        "        for k,v in metrics.items():\n"
        "            try: mlflow.log_metric(k, float(v))\n"
        "            except: pass\n"
        "        adapter_dir=out/'comment_lora'\n"
        "        trainer.model.save_pretrained(str(adapter_dir)); tok.save_pretrained(str(adapter_dir))\n"
        "        print('[OK] Saved adapter at', adapter_dir)\n"
        "        mlflow.log_artifacts(str(adapter_dir), artifact_path='comment_lora')\n"
        "        if int(hp.merge_and_save)==1:\n"
        "            merged_dir=out/'merged-fp16'; merged_dir.mkdir(parents=True, exist_ok=True)\n"
        "            merged=trainer.model.merge_and_unload(); merged.save_pretrained(str(merged_dir)); tok.save_pretrained(str(merged_dir))\n"
        "            mlflow.log_artifacts(str(merged_dir), artifact_path='merged-fp16')\n"
        "            print('[OK] Saved merged model at', merged_dir)\n"
        "        if int(hp.make_zip)==1:\n"
        "            import zipfile\n"
        "            zip_path=out.with_suffix('.zip')\n"
        "            with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as zf:\n"
        "                for p in out.rglob('*'):\n"
        "                    if p.is_file(): zf.write(str(p), str(p.relative_to(out.parent)))\n"
        "            mlflow.log_artifact(str(zip_path), artifact_path='zips')\n"
        "            print('[OK] Zipped outputs at', zip_path)\n"
        "        print('[DONE] Output dir =', out)\n"
        "        return out\n"
        "# end of training code\n"
    ))

    # 6) HF 로그인 + 학습 실행
    cells.append(nb_md_cell([
        "## 6) Hugging Face 로그인(선택) 및 학습 실행",
        "- 환경변수 `HUGGINGFACE_TOKEN`이 설정되어 있으면 비대화식 로그인 시도.",
        "- 설정된 하이퍼파라미터로 학습을 실행합니다."
    ]))
    cells.append(nb_code_cell(
        "# [6] HF login (non-interactive if token) and run training\n"
        "from huggingface_hub import login, whoami\n"
        "import os\n"
        "tok=os.getenv('HUGGINGFACE_TOKEN')\n"
        "if tok:\n"
        "    try:\n"
        "        login(token=tok, add_to_git_credential=False)\n"
        "        print('[OK] HF login for:', whoami(token=tok).get('name'))\n"
        "    except Exception as e:\n"
        "        print('[WARN] HF login:', e)\n"
        "hp = HParams(**HP)\n"
        "print('[STEP] Launch training with HP:', hp)\n"
        "out_dir = train_once(hp)\n"
        "print('[OK] Training completed. Out dir =', out_dir)\n"
        "out_dir\n"
    ))

    # 7) 간단 추론 테스트
    cells.append(nb_md_cell([
        "## 7) 간단 추론 테스트",
        "- 학습된 LoRA 어댑터를 로드하여 짧은 샘플 응답을 생성해 봅니다."
    ]))
    cells.append(nb_code_cell(
        "# [7] Quick inference test\n"
        "import torch\n"
        "from transformers import AutoTokenizer, AutoModelForCausalLM\n"
        "from peft import PeftModel\n"
        "from pathlib import Path\n"
        "adapter=Path(str(out_dir))/'comment_lora'\n"
        "base=os.getenv('BASE_MODEL','meta-llama/Meta-Llama-3.1-8B-Instruct')\n"
        "tok=os.getenv('HUGGINGFACE_TOKEN')\n"
        "print('[STEP] Load for inference...')\n"
        "tokenizer=AutoTokenizer.from_pretrained(base, use_fast=True, token=tok, trust_remote_code=True)\n"
        "if tokenizer.pad_token is None: tokenizer.pad_token=tokenizer.eos_token\n"
        "base_model=AutoModelForCausalLM.from_pretrained(\n"
        "    base, token=tok,\n"
        "    torch_dtype=(torch.bfloat16 if torch.cuda.is_available() else torch.float32),\n"
        "    device_map='auto', trust_remote_code=True)\n"
        "model=PeftModel.from_pretrained(base_model, str(adapter)); model.eval()\n"
        "prompt='Write a friendly one-line reply to someone who liked my post. No hashtags.'\n"
        "inputs=tokenizer(prompt, return_tensors='pt'); inputs={k:v.to(model.device) for k,v in inputs.items()}\n"
        "with torch.no_grad():\n"
        "    out_ids=model.generate(**inputs, max_new_tokens=80, temperature=0.8, top_p=0.9, do_sample=True,\n"
        "                           pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id)\n"
        "txt=tokenizer.decode(out_ids[0], skip_special_tokens=True)\n"
        "if txt.startswith(prompt): txt=txt[len(prompt):].lstrip()\n"
        "print('[OK] Sample output:', txt)\n"
    ))

    # 8) MLflow UI (옵션)
    cells.append(nb_md_cell([
        "## 8) (옵션) MLflow UI 실행",
        "- Colab에서 MLflow UI를 띄울 수 있으나, 포트/프록시 이슈가 있을 수 있습니다.",
        "- 필요 시 아래 명령을 주석 해제해서 실행해 보세요."
    ]))
    cells.append(nb_code_cell(
        "# [8] Optional: start MLflow UI in Colab\n"
        "# !mlflow ui --backend-store-uri $MLFLOW_TRACKING_URI --host 0.0.0.0 --port 5000\n"
    ))

    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "colab": {"name": COLAB_NOTEBOOK_TITLE},
            "kernelspec": {"name": "python3", "display_name": "Python 3"},
        },
        "cells": cells,
    }

    # 마크다운 한국어 유지를 위해 ensure_ascii=False
    return json.dumps(nb, ensure_ascii=False, indent=2)

# ---------------------------------
# Google Drive 업로드/인증
#  - 로컬에서 OAuth 브라우저 인증(최초 1회)
#  - client_secrets.json 또는 oauth_client.json을 같은 폴더에 둬야 함
# ---------------------------------
def auth_drive():
    """
    PyDrive2 로컬 웹서버 인증.
    - settings.yaml 없이 코드에서 설정 오브젝트 구성
    - client_secrets.json 또는 oauth_client.json 중 존재하는 파일 사용
    """
    print("[STEP] Google Drive authentication...")
    here = pathlib.Path(__file__).resolve().parent
    client_file = None
    for fname in ("client_secrets.json", "oauth_client.json"):
        if (here / fname).exists():
            client_file = str(here / fname)
            break
    if client_file is None:
        raise SystemExit(
            "OAuth client file not found. Put client_secrets.json (or oauth_client.json) next to run_on_colab.py"
        )

    print("[INFO] Using OAuth file:", client_file)
    settings = {
        "client_config_backend": "file",
        "client_config_file": client_file,
        "save_credentials": True,
        "save_credentials_backend": "file",
        "save_credentials_file": "pydrive2_credentials.json",
        "get_refresh_token": True,
        "oauth_scope": [
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/drive.metadata.readonly",
        ],
    }
    gauth = GoogleAuth(settings=settings)
    gauth.LocalWebserverAuth()  # 최초 1회 브라우저 인증
    print("[OK] Google auth successful.")
    return GoogleDrive(gauth)

def ensure_folder(drive, folder_name: str):
    """
    Drive/MyDrive에 폴더가 없으면 생성하고 id 반환.
    """
    print("[STEP] Ensure folder in Drive:", folder_name)
    q = f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    lst = drive.ListFile({'q': q}).GetList()
    if lst:
        print("[OK] Folder exists. id =", lst[0]['id'])
        return lst[0]['id']
    f = drive.CreateFile({'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'})
    f.Upload()
    print("[OK] Folder created. id =", f['id'])
    return f['id']

def upload_file(drive, local_path: str, parent_id: str, title: str=None, mimetype: str=None):
    """
    로컬 파일을 지정한 폴더 id 아래로 업로드.
    """
    size = os.path.getsize(local_path) if os.path.exists(local_path) else 0
    print(f"[STEP] Uploading: {local_path} ({human_size(size)}) -> folder_id={parent_id}")
    f = drive.CreateFile({'title': title or os.path.basename(local_path), 'parents': [{'id': parent_id}]})
    if mimetype:
        f['mimeType'] = mimetype
    f.SetContentFile(local_path)
    f.Upload()
    print("[OK] Uploaded. file_id =", f['id'])
    return f

# ---------------------------------
# 프로젝트 ZIP 생성
#  - 대규모/불필요 파일 제외 로직이 필요하면 여기서 확장 가능
# ---------------------------------
def zip_project(project_root: pathlib.Path, out_path: pathlib.Path):
    """
    프로젝트 폴더(ai)를 ZIP으로 묶어 상위 폴더에 생성.
    """
    print("[STEP] Zipping project:", project_root)
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for p in project_root.rglob('*'):
            if p.is_file():
                zf.write(str(p), str(p.relative_to(project_root.parent)))
    print("[OK] ZIP created:", out_path, f"({human_size(os.path.getsize(out_path))})")
    return out_path

# ---------------------------------
# 메인
# ---------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default=str(DEFAULT_PROJECT_ROOT), help="Project root path (ai)")
    ap.add_argument("--colab-dir", default=DEFAULT_COLAB_DIR, help="Drive folder name under MyDrive")
    ap.add_argument("--open", action="store_true", help="Open the generated Colab notebook URL")
    args = ap.parse_args()

    project_root = pathlib.Path(args.project_root).resolve()
    if not project_root.exists():
        raise SystemExit(f"Project root not found: {project_root}")

    print("[INFO] Project root =", project_root)

    # 1) 프로젝트 ZIP 생성
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"{project_root.name}_{stamp}.zip"   # 예: ai_YYYYmmdd_HHMMSS.zip
    local_zip = project_root.parent / zip_name
    zip_project(project_root, local_zip)

    # 2) 구글 드라이브 인증 및 업로드
    drive = auth_drive()
    folder_id = ensure_folder(drive, args.colab_dir)
    zip_file = upload_file(drive, str(local_zip), folder_id, title=zip_name)

    # 3) Colab 노트북 JSON 생성 및 업로드
    nb_json = build_notebook(
        project_zip_path=f"/content/drive/MyDrive/{args.colab_dir}/{zip_name}",
        project_root_dirname=project_root.name
    )
    # 한국어 마크다운 유지 위해 UTF-8로 저장(ensure_ascii=False 덤프)
    local_nb = project_root.parent / f"RUN_{project_root.name}_{stamp}.ipynb"
    local_nb.write_text(nb_json, encoding="utf-8")
    print("[STEP] Uploading notebook JSON:", local_nb)
    nb_file = upload_file(
        drive, str(local_nb), folder_id,
        title=local_nb.name, mimetype="application/vnd.google.colaboratory"
    )

    # 4) Colab URL 출력 및 자동 오픈(옵션)
    colab_url = f"https://colab.research.google.com/drive/{nb_file['id']}"
    print("\n[READY] Colab 링크를 열어 '런타임 → 모두 실행'을 눌러주세요.\n", colab_url)
    if args.open:
        try:
            print("[STEP] Opening browser...")
            webbrowser.open(colab_url)
        except Exception as e:
            print("[WARN] Could not open browser:", e)

    # 5) 로컬 임시 파일 정리(선택)
    try:
        print("[INFO] Cleaning local temp files...")
        # Python 3.8+: Path.unlink(missing_ok=...)
        local_zip.unlink(missing_ok=True)
        local_nb.unlink(missing_ok=True)
        print("[OK] Local temp files removed.")
    except Exception as e:
        print("[WARN] Temp cleanup:", e)

if __name__ == "__main__":
    # 윈도우 콘솔에서 로그가 섞이지 않도록 line buffering
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    main()
