import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from gazebo_msgs.srv import SetEntityState

class CircleDriveNode(Node):
    def __init__(self):
        super().__init__('circle_drive_node')

        self.cmd_vel_publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        # Gazebo 초기화 서비스 클라이언트 생성 (ROS2 Humble 기준 SetEntityState 사용)
        self.pose_client = self.create_client(SetEntityState, '/gazebo/set_entity_state')
        while not self.pose_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for /gazebo/set_entity_state service...')

        self.set_initial_position()

        self.twist_msg = Twist()
        self.twist_msg.linear.x = 0.5
        self.twist_msg.angular.z = 0.2

        self.timer = self.create_timer(0.1, self.publish_cmd_vel)
        self.get_logger().info("Circle Drive Node has been started.")

    def set_initial_position(self):
        request = SetEntityState.Request()
        request.state.name = 'simple_robot'
        request.state.pose.position.x = 0.0
        request.state.pose.position.y = -2.5
        request.state.pose.position.z = 0.1
        request.state.pose.orientation.z = 0.0
        request.state.pose.orientation.w = 1.0

        future = self.pose_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        if future.result() is not None:
            self.get_logger().info("Initial position set successfully.")
        else:
            self.get_logger().error("Failed to set initial position.")

    def publish_cmd_vel(self):
        self.cmd_vel_publisher.publish(self.twist_msg)

def main(args=None):
    rclpy.init(args=args)
    node = CircleDriveNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
