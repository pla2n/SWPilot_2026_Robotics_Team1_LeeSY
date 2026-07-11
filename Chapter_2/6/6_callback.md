# [과제 2-6] ROS2 타이머와 콜백 함수 활용 실습 (지속 동작 로봇 만들기)

---

## 1. 콜백(Callback) 함수의 개념

- **일반적인 정의:** 프로그래밍에서 다른 함수의 인자(Argument)로 전달되어, 특정 이벤트가 발생하거나 조건이 충족되었을 때 시스템이나 다른 함수에 의해 나중에 호출(실행)되는 함수를 의미한다.
- **비유적 설명:** 식당에서 진동벨을 받는 것과 같다. 음식이 언제 나올지 계속 주방을 쳐다보며 기다리는 것(동기식)이 아니라, 진동벨(타이머 이벤트)이 울리면 그때 음식을 가지러 가는 행동(콜백 함수)을 취하는 효율적인 방식이다.

---

## 2. ROS2 타이머(Timer)의 개념 및 활용

- **개념:** 로봇은 단발성 명령 수행이 아니라 지속적으로 센서를 읽고 모터를 제어해야 한다. ROS2의 타이머는 개발자가 지정한 시간 주기(Period)마다 특정 콜백 함수를 반복적으로 깨워 실행시켜 주는 백그라운드 스케줄러 역할을 한다.
- **생성 방법:** `Node` 객체의 내장 메서드인 `self.create_timer(주기_초, 콜백함수명)`를 사용하여 생성한다. 이 타이머가 생성되면 `rclpy.spin()`이 동작하는 동안 정확한 주기에 맞춰 콜백 함수를 무한 반복 실행한다.

---

## 3. 제어 노드 파이썬 코드 구현 (`timer_test.py`)

`~/ros2_ws/src/my_robot_controller/my_robot_controller/` 경로에 `timer_test.py` 파일을 생성하고 아래 코드를 작성하였다.

```python
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

class LoggingNode(Node):
    def __init__(self):
        super().__init__('timer_node')
        # 상태를 저장하고 두 콜백 함수가 공유할 클래스 속성(인스턴스 변수) 초기화
        self.counter = 0

        # 2초마다 호출될 타이머와 3초마다 호출될 타이머 각각 생성
        self.create_timer(2.0, self.two_seconds_callback)
        self.create_timer(3.0, self.three_seconds_callback)

    def two_seconds_callback(self):
        self.counter += 1
        self.get_logger().info(f'2 seconds passed : {self.counter}')

    def three_seconds_callback(self):
        self.counter -= 1
        self.get_logger().info(f'3 seconds passed : {self.counter}')

def main(args=None):
    rclpy.init(args=args)
    node = LoggingNode()
    rclpy.spin(node) # 프로그램이 종료되지 않도록 무한 대기하며 타이머 이벤트 처리
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 3.1 카운터 변수(`counter`) 공유 메커니즘

서로 다른 시간 주기를 가진 2초 콜백 함수와 3초 콜백 함수가 하나의 카운터 값을 올바르게 조작하기 위해, `counter` 변수를 파이썬 클래스의 인스턴스 속성(`self.counter`)으로 정의하였다. 이를 통해 객체 내부의 모든 메서드가 동일한 변수에 접근하고 상태를 완벽하게 공유할 수 있다.

---

## 4. `setup.py` 파일 수정 및 진입점 등록

새로 작성한 파이썬 스크립트를 ROS2 시스템이 인식할 수 있도록 `setup.py`의 `console_scripts` 영역에 노드 매핑 규칙을 추가하였다. 기존에 등록했던 `logging_node` 아래에 줄바꿈표(콤마)를 넣고 추가한다.

```python
    entry_points={
        'console_scripts': [
            'logging_node = my_robot_controller.logging:main',
            'timer_node = my_robot_controller.timer_test:main'
        ],
    },
```

---

## 5. [부록] 평가 가이드 기반 핵심 이해도 검증

### Q1. 구현한 프로그램에서 `rclpy.spin()` 함수는 어떤 역할을 하는가?

- **답변:** 프로세스가 즉시 종료되지 않도록 메인 스레드를 무한 루프 상태(대기)로 잡아두며, 타이머나 외부 메시지 등의 이벤트가 발생할 때마다 ROS2 시스템이 노드 클래스 내부에 정의된 콜백 함수들을 스케줄링하고 실행할 수 있도록 제어권을 넘겨주는 핵심 엔진 역할을 합니다.

### Q2. 파이썬 콜백 함수의 개념에 대해서 설명해보자.

- **답변:** 다른 함수의 인자(파라미터)로 전달되는 함수를 말하며, 직접 명시적으로 호출하는 것이 아니라 타이머 만료나 데이터 수신 등 특정 조건(이벤트)이 충족되었을 때 시스템에 의해 수동적으로 호출되어 실행되는 함수입니다.

### Q3. 2초마다 로그를 남기도록 구현한 방식을 설명해보자.

- **답변:** `two_seconds_callback`이라는 콜백 함수(메서드) 내부에 로그를 남기는 코드를 작성한 뒤, 노드의 `__init__` 초기화 단계에서 `self.create_timer(2.0, self.two_seconds_callback)`를 호출하여 2.0초의 주기마다 해당 메서드가 시스템에 의해 자동 호출되도록 메커니즘을 구성했습니다.

### Q4. ROS2에서 타이머와 콜백함수를 사용해 로봇이 지속적으로 동작하게 하는 메커니즘을 설명해보자.

- **답변:** 로봇은 수십 헤르츠(Hz)의 빠른 속도로 센서 데이터를 읽고 모터 구동 값을 계산해야 합니다. `while True` 같은 단순 무한 루프를 쓰면 시스템이 먹통이 될 수 있으므로, ROS2는 타이머를 통해 정해진 시간 주기로 비동기 콜백 함수를 실행하여 다른 통신(통합 네트워크)을 방해하지 않고도 규칙적이고 지속적인 로봇 제어 알고리즘을 수행하도록 설계되어 있습니다. 만약 주기를 짧게(예: 0.1초) 설정하면 콜백이 1초에 10번 실행되며 훨씬 더 조밀하게 모터를 제어할 수 있습니다.
