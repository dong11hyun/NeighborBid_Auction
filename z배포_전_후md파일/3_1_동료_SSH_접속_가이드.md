# 동료 서버 등록 및 공유 폴더 설정 가이드

이 가이드는 동료를 나의 서버에 등록하고, SSH 키를 통해 안전하게 접속하며, 공동 작업을 위한 공유 폴더를 설정하는 과정을 설명합니다.

---

## � 1. 동료에게 준비 시킬 것 (딱 1가지)

동료에게 **"SSH 공개키(Public Key)를 보내달라"**고 요청하세요.

### 동료 PC (Windows / Git Bash or PowerShell)에서 실행
동료는 아래 명령어를 자신의 터미널에서 실행해야 합니다.

```bash
ssh-keygen -t rsa -b 4096
```

- **입력 요청 시**: 그냥 `Enter` 키를 3번 누르면 됩니다. (경로 및 비밀번호 설정 스킵)
- **생성된 파일**:
    - `id_rsa` (비밀키): **절대 공유 금지**
    - `id_rsa.pub` (공개키): **이 파일의 내용을 복사해서 나에게 전달**

---

## 🔹 2. 실제 작업 흐름 (서버 관리자가 수행)

### ① 서버에 동료 계정 생성

서버에 접속하여 새로운 사용자를 추가하고 관리자 권한을 부여합니다.

```bash
sudo adduser teammate
sudo usermod -aG sudo teammate   # 관리자 권한(sudo) 부여
```

### ② SSH 키 등록 및 설정

각자 자신의 SSH 키로 접속하게 됩니다.
- **나**: `~/.ssh/id_rsa` 사용
- **동료**: 동료의 공개키 사용

동료를 위한 SSH 디렉토리를 생성하고 권한을 설정합니다.

```bash
# 디렉토리 생성 및 권한 설정
sudo mkdir /home/teammate/.ssh
sudo chmod 700 /home/teammate/.ssh   # .ssh 디렉토리는 소유자(teammate)만 접근 가능
```

동료의 공개키를 등록합니다.

```bash
# 편집기 열기
sudo nano /home/teammate/.ssh/authorized_keys
```

> **Nano 편집기 내에서**: 동료가 보내준 `id_rsa.pub` (공개키) 내용을 그대로 붙여넣고 저장(`Ctrl+O` -> `Enter` -> `Ctrl+X`)하세요.

**권한 설정 (필수 - 안 하면 접속 실패함)**

```bash
# 파일 권한 설정 (소유자만 읽기/쓰기 가능)
sudo chmod 600 /home/teammate/.ssh/authorized_keys

# 소유권 변경 (root -> teammate)
sudo chown -R teammate:teammate /home/teammate/.ssh
```

---

## 🔹 3. 비밀번호 로그인 차단 (보안 필수)

SSH 설정을 수정하여 비밀번호 로그인을 막고, 오직 키 파일로만 접속하도록 설정합니다.

### SSH 설정 파일 수정

```bash
sudo nano /etc/ssh/sshd_config
```

아래 항목을 찾아 다음과 같이 변경하세요. (주석 `#`이 있다면 제거)

```ssh
PasswordAuthentication no
PubkeyAuthentication yes
```

### SSH 재시작

설정 변경 사항을 적용합니다.

```bash
sudo systemctl restart ssh
```

👉 **결과**: 비밀번호 로그인 ❌ / 키 로그인 ⭕

---

## 🔹 4. 공유 폴더 설정

공동 작업을 위한 폴더를 만들고 권한을 설정합니다.

### ① 공유 폴더 새로 만들기

```bash
sudo mkdir /apps
```

### ② 소유권을 공동으로 바꾸기 (가장 단순한 방법)

가장 단순한 방법으로, 두 사용자 모두 `sudo` 권한이 있을 때 유용합니다.

```bash
# /apps 와 그 안의 모든 파일/폴더의 소유자: ubuntu, 그룹: ubuntu
sudo chown -R ubuntu:ubuntu /apps

# /apps 전체 권한 설정 (그룹 멤버에게 쓰기 권한 부여)
sudo chmod -R 775 /apps
```

> **참고**: `chown`은 파일/폴더의 소유자(user)와 소유 그룹(group)을 바꾸는 명령어이며, `-R` 옵션은 하위 폴더와 파일까지 모두(재귀적으로) 적용한다는 의미입니다.
