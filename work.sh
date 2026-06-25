#!/bin/bash

# 에러 발생 시 스크립트 중단 (단, 백업 실패 등은 유연하게 처리)
set -e

echo "===================================================="
echo " [안전 모드] 도커 보안 설정 스크립트를 시작합니다."
echo "===================================================="

# 0. Root 권한 체크
if [ "$EUID" -ne 0 ]; then
  echo "❌ 이 스크립트는 sudo 권한(root)으로 실행해야 합니다."
  exit 1
fi

# --------------------------------------------------
# [131 페이지] auditd 설치 및 도커 서비스 감시 설정
# --------------------------------------------------
echo -e "\n🔹 [131p] auditd 설치 및 도커 서비스 감사 규칙 설정 중..."

# audit 패키지 설치
dnf install audit -y
systemctl enable --now auditd

# docker.service 파일 경로 자동 확인
DOCKER_SERVICE_PATH=$(systemctl show -p FragmentPath docker.service | cut -d= -f2)

if [ -n "$DOCKER_SERVICE_PATH" ]; then
    echo "✔ 도커 서비스 경로 확인됨: $DOCKER_SERVICE_PATH"
    
    # audit 규칙 디렉터리 생성 확인
    mkdir -p /etc/audit/rules.d
    
    # 기존 규칙 파일이 존재한다면 백업 후 새로 생성
    if [ -f /etc/audit/rules.d/docker.rules ]; then
        echo "💡 기존 docker.rules 파일이 존재하여 백업합니다. (.bak)"
        cp /etc/audit/rules.d/docker.rules /etc/audit/rules.d/docker.rules.bak
    fi
    
    echo "-w $DOCKER_SERVICE_PATH -k docker" > /etc/audit/rules.d/docker.rules
    augenrules --load
    echo "✔ auditd 감사 규칙 반영 완료."
else
    echo "⚠️ 도커 서비스 경로를 찾을 수 없습니다. 도커가 설치되어 있는지 확인하세요."
fi


# --------------------------------------------------
# [133, 135 페이지] 도커 데몬 설정 (기존 파일이 있을 경우 안전하게 병합)
# --------------------------------------------------
echo -e "\n🔹 [133p/135p] Docker 데몬 설정 (/etc/docker/daemon.json) 작성 중..."

# 도커 설정 디렉터리가 없으면 생성
mkdir -p /etc/docker

# 기존 daemon.json 파일이 존재할 경우 백업
if [ -f /etc/docker/daemon.json ]; then
    echo "💡 기존 daemon.json 파일이 존재하여 백업합니다. (/etc/docker/daemon.json.bak)"
    cp /etc/docker/daemon.json /etc/docker/daemon.json.bak
fi

# 교재에 제시된 설정값을 반영하여 daemon.json 덮어쓰기
cat << 'EOF' > /etc/docker/daemon.json
{
  "selinux-enabled": true,
  "bip": "192.168.1.5/24",
  "fixed-cidr": "192.168.1.5/25",
  "fixed-cidr-v6": "2001:db8::/64",
  "mtu": 1500,
  "default-gateway": "10.20.1.1",
  "default-gateway-v6": "2001:db8:abcd::89",
  "dns": ["10.20.1.2", "10.20.1.3"]
}
EOF
echo "✔ daemon.json 파일 신규 설정 완료."


# --------------------------------------------------
# [133 페이지] container-selinux 패키지 설치 및 SELinux 영구 설정
# --------------------------------------------------
echo -e "\n🔹 [133p] SELinux 관련 보안 정책 및 도커 연동 설정 중..."
dnf install container-selinux -y

# SELinux 설정 파일 존재 여부 확인 후 수정
if [ -f /etc/selinux/config ]; then
    # 기존 설정 백업
    cp /etc/selinux/config /etc/selinux/config.bak
    
    if grep -q "^SELINUX=disabled" /etc/selinux/config; then
        sed -i 's/^SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config
        echo "⚠️ [주의] 기존에 SELinux가 완전히 꺼져(disabled) 있었습니다."
        echo "    설정 파일을 enforcing으로 변경했으니, 스크립트 종료 후 'sudo reboot'으로 서버를 재부팅해야 완전히 적용됩니다."
    else
        # 이미 permissive나 enforcing 이라면 즉시 실행 모드 변경 시도
        sed -i 's/^SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config
        setenforce 1 || true
        echo "✔ SELinux Enforcing 상태 실시간 적용 완료."
    fi
else
    echo "⚠️ /etc/selinux/config 파일을 찾을 수 없습니다. SELinux가 이 시스템에 설치되어 있는지 확인하세요."