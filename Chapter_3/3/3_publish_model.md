# [과제 3-3] 로봇 상태 퍼블리셔 구현 및 TF 게시 심층 보고서

## 1. 로봇의 상태 게시(Publish)의 진정한 의미와 방법

### 1.1. 로봇의 상태를 게시한다는 것의 의미 (정적 데이터와 동적 데이터의 결합)

ROS2 환경에서 로봇을 제어하고 시뮬레이션하기 위해서는 두 가지 정보가 필요합니다.

1. **정적 정보 (URDF):** 로봇의 팔 길이, 바퀴의 크기, 관절의 연결 위치 등 변하지 않는 '뼈대' 정보.
2. **동적 정보 (상태 데이터):** 로봇의 바퀴가 현재 몇 도(Rad) 돌아갔는지, 팔이 얼마나 펴졌는지에 대한 '실시간 물리량'.

즉, **'로봇의 상태를 게시(Publish)한다'**는 것은 시뮬레이터(RViz2 등)나 다른 제어 알고리즘이 로봇의 현재 자세를 실시간으로 파악할 수 있도록, **각 관절(Joint)의 현재 위치(각도), 속도, 힘(Torque) 등의 데이터를 ROS2 네트워크 상에 지속적으로 브로드캐스팅(퍼블리시)** 하는 행위를 의미합니다.

### 1.2. URDF로 정의된 로봇의 상태를 시뮬레이터에 게시하는 방법

정적인 URDF 모델에 생명력을 불어넣어 시뮬레이터에 표현하려면 다음의 파이프라인을 거쳐야 합니다.

1. **상태 생성 (Joint State Publisher):** 개발자가 작성한 파이썬 노드(또는 실제 모터 엔코더)가 각 관절의 실시간 회전/이동 값을 수집하여 `/joint_states` 토픽으로 퍼블리시합니다.
2. **좌표 변환 (Robot State Publisher):** ROS2가 제공하는 내장 노드인 `robot_state_publisher`가 위에서 생성된 동적 토픽(`/joint_states`)과 정적 파일(URDF)을 동시에 구독(Subscribe)합니다.
3. **TF 게시:** 위 두 정보를 결합하여 로봇의 모든 부품(링크) 간의 3차원 위치 관계(TF, Transform)를 계산해 `/tf` 토픽으로 게시하면, 시뮬레이터가 이를 바탕으로 화면에 움직이는 로봇을 렌더링합니다.

---

## 2. /joint_states 토픽과 robot_state_publisher의 상호작용

### 2.1. `/joint_states` 토픽의 개념과 용도

- **개념:** ROS2에서 로봇 관절의 상태를 전달하기 위해 약속된 표준 메시지 타입(`sensor_msgs/msg/JointState`)을 사용하는 토픽입니다.
- **구조 및 용도:** 이 메시지는 타임스탬프(`header`), 관절의 이름(`name`), 현재 각도나 거리(`position`), 회전 속도(`velocity`), 모터에 가해지는 힘(`effort`)을 배열 형태로 담아 전달합니다. 로봇의 모든 관절 상태를 하나의 메시지로 묶어 시스템 전체에 공유하는 척추 역할을 합니다.

### 2.2. `robot_state_publisher` 노드의 핵심 역할 (순기구학 연산)

이 노드는 단순히 데이터를 전달하는 것을 넘어, 로봇 공학에서 매우 중요한 **순기구학(Forward Kinematics) 연산**을 대신해 줍니다.
바퀴가 회전하면 바퀴 표면의 좌표계도 함께 돌아가야 합니다. `robot_state_publisher`는 URDF에 적힌 링크 간의 거리 정보와 `/joint_states`로 들어오는 실시간 관절 각도를 수학적으로 계산하여, 부모 링크 대비 자식 링크가 현재 3차원 공간상 어디에 위치하고 어느 곳을 바라보는지(TF Tree)를 자동 연산해 뿌려줍니다.

### 2.3. 만약 `robot_state_publisher`를 사용하지 않는다면?

이 노드가 제공되지 않는다면 개발자가 겪어야 할 작업은 매우 가혹합니다.
로봇에 부품(링크)이 10개라면, 각 부품 간의 x, y, z 거리 오프셋과 roll, pitch, yaw 회전량을 삼각함수와 회전 행렬(Rotation Matrix)을 이용해 **개발자가 직접 코드로 하나하나 계산**해야 합니다. 부품이 움직일 때마다 이 모든 행렬을 다시 계산해서 각각 `/tf` 토픽으로 쏴주어야 하는 엄청난 수학적/컴퓨팅 리소스 낭비가 발생합니다.

---

## 3. 코드 분석 및 구현 내용

이번 실습에서 작성한 파이썬 노드(`joint_state_publisher.py`)는 실제 로봇의 모터가 없는 시뮬레이션 환경이므로, 코드를 통해 임의의 가짜 속도와 위치 값을 만들어내어 바퀴가 굴러가는 것처럼 구현했습니다.

### 3.1. 파이썬 퍼블리셔 로직 분석

- `create_timer(0.1, ...)`: 0.1초(10Hz)마다 `publish_joint_states` 함수를 실행하여 실시간성을 보장합니다.
- `msg.name = ['left_wheel_joint', 'right_wheel_joint']`: URDF에 명시했던 관절의 이름을 정확히 매칭시킵니다.
- `self.joint_position += self.joint_velocity * 0.1`: 0.1초마다 속도만큼 위치(각도) 값을 누적(증가)시킵니다. 이 누적된 값이 퍼블리시되면서 RViz2 상에서 바퀴가 계속해서 회전하는 애니메이션이 만들어집니다. 양쪽 바퀴가 반대로 돌지 않게 하기 위해 우측 바퀴에는 `-self.joint_position`으로 음수 처리를 했습니다.

### 3.2. Launch 파일(`display.launch.py`)의 구성 의도

하나의 런치 파일을 통해 3개의 노드를 동시에 실행하도록 구성했습니다.

1. `robot_state_publisher`: URDF 파일을 읽어서 시스템에 대기시킵니다.
2. `joint_state_publisher` (작성한 파이썬 노드): 실시간 바퀴 회전 데이터를 생성합니다.
3. `rviz2`: 시각화 도구를 띄우고, 미리 저장해 둔 `.rviz` 설정 파일을 물려주어 실행 즉시 로봇 모델이 보이도록 자동화했습니다.

---

## 4. 전체 구현 소스 코드

### 4.1. joint_state_publisher.py

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

class JointStatePublisher(Node):
    def __init__(self):
        super().__init__('joint_state_publisher')
        # /joint_states 토픽으로 JointState 타입의 메시지를 발행하는 퍼블리셔 생성
        self.publisher_ = self.create_publisher(JointState, '/joint_states', 10)
        # 0.1초(10Hz)마다 상태를 발행하는 타이머 콜백 설정
        self.timer = self.create_timer(0.1, self.publish_joint_states)

        # 초기 위치 및 속도 설정 (임의의 구동 상태 시뮬레이션)
        self.joint_position = 0.0
        self.joint_velocity = 0.1

    def publish_joint_states(self):
        msg = JointState()
        # 현재 시간을 메시지 헤더에 기록 (TF 동기화에 필수)
        msg.header.stamp = self.get_clock().now().to_msg()
        # URDF에 정의된 조인트 이름과 1:1 매칭
        msg.name = ['left_wheel_joint', 'right_wheel_joint']

        # 현재 위치와 속도 입력 (우측 바퀴는 대칭 동작을 위해 -값 적용)
        msg.position = [self.joint_position, -self.joint_position]
        msg.velocity = [self.joint_velocity, -self.joint_velocity]
        msg.effort = [0.0, 0.0] # 가해지는 물리적 힘 (본 실습에서는 생략)

        # 다음 발행 주기를 위해 각도(위치) 값 업데이트 누적
        self.joint_position += self.joint_velocity * 0.1
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = JointStatePublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```
