# 5. Gazebo + ROS2 연동 — 원 궤도 주행 로봇

## 1. URDF의 Inertia, Collision 태그

**Collision 태그**

- 물리 엔진이 "충돌을 계산할 때만" 쓰는 도형. Visual(눈에 보이는 모양)과 분리되어 있는 이유는, 실제 렌더링용 3D 모델은 정점이 많아서 그대로 충돌 계산에 쓰면 시뮬레이션이 느려지기 때문.
- 예: 자동차 게임에서 화면에는 디테일한 자동차가 보이지만, 충돌 판정은 그 자동차를 감싸는 단순한 상자(박스)로 계산하는 것과 같은 원리.

**Inertial(질량+관성) 태그**

- `mass`: 물체의 질량(kg)
- `origin`: 무게중심 위치
- `inertia`(관성모멘트, Inertia Tensor): "회전시키기 얼마나 어려운가"를 나타내는 값. `ixx, iyy, izz`(대각 성분)와 `ixy, ixz, iyz`(비대각 성분, 대칭축이 있으면 보통 0)로 구성.
  - 비유: 같은 무게라도 아령처럼 무게가 바깥쪽에 몰려 있으면 돌리기 어렵고(관성모멘트 큼), 공처럼 무게가 중심에 몰려 있으면 돌리기 쉽다(관성모멘트 작음).
  - 계산 공식(균일 밀도 기준):
    - 직육면체(가로w, 세로d, 높이h): `Ixx=m(d²+h²)/12`, `Iyy=m(w²+h²)/12`, `Izz=m(w²+d²)/12`
    - 원기둥(반지름r, 길이h): `Ixx=Iyy=m(3r²+h²)/12`, `Izz=mr²/2`
    - 구(반지름r): `Ixx=Iyy=Izz=2mr²/5`
  - `simple_robot.urdf`에서는 이 공식으로 몸체(박스)와 바퀴(원기둥)의 값을 실제로 계산해서 넣었다. (본 문서 하단 소스 참고)
- **왜 필요한가**: Inertia/Collision 값이 없거나 비현실적이면(0에 가깝거나 너무 크면) 시뮬레이션에서 로봇이 발작하듯 튀거나(NaN 에러), 반대로 전혀 안 움직이는 문제가 생긴다. 실무에서도 디지털 트윈이나 로봇 시뮬레이션을 만들 때 실제 부품의 질량/치수를 CAD에서 뽑아 반영해야 시뮬레이션 결과가 실제 로봇 거동과 맞아떨어진다.

## 2. Gazebo와 ROS2의 연동 방식

- 핵심 중개자는 **`gazebo_ros` 패키지**(정확히는 `gazebo_ros_pkgs`)다. Gazebo는 원래 ROS를 몰라도 되는 독립 시뮬레이터인데, 이 패키지가 "Gazebo 플러그인 ↔ ROS2 토픽/서비스"를 서로 변환해주는 다리 역할을 한다.
- 흐름: URDF/SDF의 `<gazebo><plugin>` 태그에 원하는 컨트롤러 플러그인을 등록 → Gazebo가 로딩될 때 그 플러그인의 `.so`(공유 라이브러리) 파일을 불러옴 → 플러그인 내부 코드가 ROS2 노드처럼 동작하며 토픽을 publish/subscribe함 → 우리가 만든 일반 ROS2 노드(`circle_drive_node.py`)는 평소처럼 토픽만 주고받으면 됨(Gazebo인지 실제 로봇인지 신경 안 써도 됨).
- 비유: 플러그인은 "번역기"다. 로봇 쪽(Gazebo 물리엔진)은 힘/토크 단위로 말하고, 우리 프로그램(ROS2)은 "초속 0.5m로 가" 같은 토픽 언어로 말하는데, 플러그인이 이 둘을 통역해준다.
- 실무 연결: 실제 회사에서도 "실물 로봇 컨트롤러 코드"를 그대로 시뮬레이터에 올려서 검증(SIL/HIL 테스트)하는 이유가 이것 때문이다. 인터페이스(토픽)만 같으면 코드 수정 없이 시뮬레이션 → 실기기로 그대로 전환할 수 있다.

## 3. ROS2로 Gazebo에 로봇을 배치하는 방법

두 가지 방식이 있다.

1. **`spawn_entity.py` 노드 사용 (이번 과제에서 채택)**
   - `gazebo_ros` 패키지가 제공하는 실행 파일. `-entity`(이름), `-topic`(robot_description 토픽에서 URDF 읽기) 또는 `-file`(URDF 파일 경로), `-x/-y/-z`(초기 위치) 인자를 받는다.
   - Launch File에서 `robot_state_publisher`가 먼저 URDF를 `/robot_description` 토픽으로 게시하고, `spawn_entity.py`가 그 토픽을 구독해서 Gazebo 내부의 `/spawn_entity` 서비스를 호출하는 구조.
2. **World 파일에 로봇을 미리 박아두는 방식**
   - `.world` SDF 파일 안에 로봇 모델을 직접 include 해두는 방법. 초기 배치 로봇이 고정적일 때 씀. 이번 과제처럼 launch에서 동적으로 스폰하는 방식이 더 유연하다(위치, 여러 대 스폰 등 제어 가능).

`circle_drive.launch.py`에서는 Gazebo 실행 → `robot_state_publisher` 실행 → 3초 대기 후 `spawn_entity.py` 실행 → 5초 대기 후 제어 노드 실행 순서로 구성했다(Gazebo가 완전히 켜지기 전에 스폰을 시도하면 서비스 호출이 실패하기 때문에 `TimerAction`으로 지연시킴).

## 4. Gazebo 플러그인 개념 · 용도 · 사용법

- **개념**: Gazebo 물리엔진에 끼워 넣는 C++로 작성된 동적 라이브러리(`.so` 파일). 시뮬레이션 스텝마다 호출되어 센서 값을 만들거나, 모터에 힘을 가하거나, ROS2와 통신하는 등의 커스텀 동작을 추가한다.
- **왜 쓰는가**: Gazebo 코어 자체는 "물리 법칙 계산기"일 뿐이라 로봇 특유의 동작(바퀴 두 개로 조향하기, 라이다처럼 레이저를 쏘고 거리 재기 등)은 모른다. 이런 로봇 특화 기능을 플러그인 형태로 추가해서 확장하는 구조.
- 종류: Model 플러그인(로봇 전체), Sensor 플러그인(카메라·라이다 등), World 플러그인(환경 전체) 등.
- **사용법**: URDF/SDF의 `<gazebo>` 태그 안에 `<plugin name="..." filename="라이브러리이름.so">`로 선언하고, 그 플러그인이 요구하는 하위 파라미터 태그(조인트 이름, 바퀴 간격 등)를 채워 넣으면 Gazebo 로딩 시 자동으로 적용된다. 별도의 빌드나 코드 작성 없이 이미 컴파일된 표준 플러그인(`libgazebo_ros_diff_drive.so` 등)을 그대로 가져다 쓸 수 있다.

## 5. diff_drive_controller (`libgazebo_ros_diff_drive.so`)

- 좌우 바퀴 각각의 속도를 독립 제어해서 "차동 구동(differential drive)" 방식으로 로봇을 움직이는 표준 플러그인.
- 입력: `geometry_msgs/msg/Twist` 메시지를 `/cmd_vel` 토픽으로 받음 (`linear.x` = 전진 속도, `angular.z` = 회전 각속도).
- 내부적으로 `linear.x`, `angular.z`를 좌우 바퀴 각속도로 변환하는 공식:
  - `왼쪽 바퀴 각속도 = (linear.x - angular.z * wheel_separation/2) / wheel_radius`
  - `오른쪽 바퀴 각속도 = (linear.x + angular.z * wheel_separation/2) / wheel_radius`
- 출력: `/odom` 토픽(추정 위치/속도)과 `odom → base_link` TF를 게시(옵션으로 on/off 가능).
- 주요 파라미터: `left_joint`/`right_joint`(구동 조인트 이름), `wheel_separation`(바퀴 간 거리), `wheel_diameter`(바퀴 지름), `max_wheel_torque`, `update_rate`.

## 6. 파이썬 제어 프로그램에서의 제어 방식

`circle_drive_node.py`는 단순히 `/cmd_vel` 토픽에 일정한 `Twist` 메시지(선속도+각속도)를 0.1초 주기로 계속 publish 한다. diff_drive_controller 플러그인이 이 값을 받아 좌우 바퀴 속도로 변환해 로봇을 굴리므로, 결과적으로 로봇은 반지름이 일정한 원을 그리며 주행한다.

- 원의 반지름 공식: `R = linear.x / angular.z`
  - 예) `linear.x=0.5 m/s`, `angular.z=0.2 rad/s` → `R = 2.5 m`
- **원을 더 작게 만들려면**: `linear.x`(선속도)를 줄이거나 `angular.z`(각속도)를 키우면 된다. 반대로 원을 크게 하려면 선속도를 키우거나 각속도를 줄이면 된다.
- 코드에서는 이 두 값을 ROS2 파라미터(`linear_speed`, `angular_speed`)로 빼두어서, 코드를 다시 빌드하지 않고 `--ros-args -p` 옵션이나 launch 파라미터로 바로 바꿀 수 있게 했다. (실무에서도 튜닝 값은 하드코딩하지 않고 파라미터/설정 파일로 분리하는 것이 표준적인 방식이다.)

## 7. 빌드 및 실행 절차

```bash
# 워크스페이스 루트에서
cd ~/robot_ws
colcon build --packages-select circle_drive_pkg
source install/setup.bash

# 실행
ros2 launch circle_drive_pkg circle_drive.launch.py
```

**확인 방법**

- Gazebo 창이 뜨고 로봇 모델이 스폰되는지 확인
- 별도 터미널에서 `ros2 topic echo /odom`으로 위치가 원형으로 변하는지 확인
- `ros2 topic echo /cmd_vel`으로 제어 노드가 값을 정상 게시하는지 확인
- Gazebo 뷰에서 로봇이 실제로 원을 그리며 도는지 육안 확인
