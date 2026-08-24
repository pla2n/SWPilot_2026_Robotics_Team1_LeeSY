# Gazebo 시뮬레이터 환경(World) 구성 및 로봇 제어

## 1. Gazebo 시뮬레이션 환경 파일 구조
Gazebo 환경 파일은 주로 XML 기반의 SDF(Simulation Description Format) 형식을 사용한다. 
최상위 `<sdf>` 태그 안에 `<world>` 또는 `<model>` 태그가 위치하며, 그 하위에 물리적 속성(`<inertial>`), 시각적 외형(`<visual>`), 충돌 영역(`<collision>`) 등을 정의한다.

## 2. Gazebo 시뮬레이션 환경 제작 방법
*   **텍스트 에디터 직접 작성**: SDF 형식의 XML 코드를 직접 작성하여 환경을 정밀하게 구성하는 방법이다.
*   **Gazebo GUI 툴 활용**: Gazebo 실행 후 상단 메뉴의 'Building Editor'나 'Model Editor'를 사용하여 3D 환경에서 벽, 바닥 등을 시각적으로 배치하고 `.world` 또는 `.sdf` 파일로 저장하는 방법이다.
*   **외부 파일 연동**: 블렌더(Blender) 등의 3D 모델링 툴에서 제작한 메쉬 파일(.dae, .stl)을 불러오거나 2D 이미지를 기반으로 지형(Heightmap)을 생성하는 방법도 존재한다.

## 3. 월드 좌표계와 로컬 좌표계의 관계
*   **월드 좌표계(World Coordinate)**: 시뮬레이션 공간 전체의 절대적인 기준점(0,0,0)을 갖는 고정 좌표계다. 환경 내 모든 객체의 절대 위치를 결정한다.
*   **로컬 좌표계(Local Coordinate)**: 로봇의 특정 부위(예: `base_link`)를 원점으로 삼는 상대 좌표계다. 로봇 중심의 센서 데이터 처리에 사용된다.
*   **관계**: 로봇을 환경에 배치하거나 이동시킬 때, 로봇의 로컬 좌표계를 월드 좌표계 기준으로 변환(Transform, TF)해야 정확한 시뮬레이션 및 제어가 가능하다.

## 4. 환경 파일과 함께 시뮬레이터 실행 방법
*   **CLI 실행**: 터미널에서 `gazebo worlds/world.sdf` 명령어를 입력하여 실행한다.
*   **Launch 파일 활용**: ROS2 launch 파일의 `ExecuteProcess` 액션에 `cmd=["gazebo", "--verbose", "-s", "libgazebo_ros_factory.so", "worlds/world.sdf"]` 형태로 인자를 전달하여 로봇 노드 등과 함께 일괄 실행한다.

## 5. 경로 생성 및 설정값 반영
이전 과제의 파이썬 제어 노드에서 선속도 $V = 0.5$, 각속도 $\omega = 0.2$로 설정했다. 
등속 원운동의 반지름 $R = V / \omega$ 공식에 따라 로봇이 그리는 궤적의 중심 반지름은 2.5m다.
이를 반영하여 `world.sdf`에 반경 2.35m의 내부 원과 반경 2.65m의 외부 원을 생성해 두께 0.3m의 원형 트랙을 구현했다. 초기 위치는 반경 2.5m 지점에 스폰되도록 제어 노드의 초기 Pose 값을 설정했다.
