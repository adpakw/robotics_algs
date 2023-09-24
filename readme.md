Инструкция по установке ROS и запуску алгоритмов

Инструкция по запуску алгоритмов Bug1 и Bug2

Необходимые преустановленные файлы и пакеты:

1. Установленная система для работы с ROS Noetic и созданный workspace(http://wiki.ros.org/ROS/Tutorials) 

2. Пакеты для работы с turtlebot3
https://emanual.robotis.com/docs/en/platform/turtlebot3/quick-start/

3.Пакеты для работы в gazebo с turtlebot3(все туториалы должны быть для ros noetic)
https://emanual.robotis.com/docs/en/platform/turtlebot3/simulation/#gazebo-simulation
https://emanual.robotis.com/docs/en/platform/turtlebot3/quick-start/

4. Python3 для запуска скриптов, написаных на нём

Далее я предлагаю два способа установки пакета с алгоритмами:



Первый (предпочтительный)

https://drive.google.com/drive/folders/1DUjp2fUDPwOOscECeC9iXsU4qcShlL1Q?usp=sharing

1. Скачать архив с пакетом bug_alg с google disk

2. Разархивировать его в catkin_ws/src
(вместо catkin_ws должно быть название Вашего воркспейса)

3.Проверить, что все файлы в установленном пакете executable

Для этого заходим в scripts и в Properties/permissions ставим галочку около allow executing file as program
Аналогично повторяем с CMAKE, xml, setup.py файлами в самом пакете, bug_alg, launch файлами в launch и файлом по адресу ~/catkin_ws/src/bug_alg/src/bug_alg/__init__.py 

(ДОБАВИЛ НОВОЕ)
chmod +x src/bug_alg/CMakeLists.txt
chmod +x src/bug_alg/package.xml
chmod +x src/bug_alg/setup.py
chmod +x src/bug_alg/launch/*.launch
chmod +x src/bug_alg/scripts/*.py
chmod +x src/bug_alg/src/bug_alg/__init__.py
(ДОБАВИЛ НОВОЕ)

4. Открываем terminal и пишем команды 

cd ~/catkin_ws/

catkin_make

source devel/setup.bash

5. Иногда возникают проблемы с catkin_make и приходится повторять 4 шаг несколько раз



Второй способ установки алгоритмов

1. Следуя tutorials на http://wiki.ros.org/ROS/Tutorials создать собственные пакеты для работы с ROS

Вручную или с помощью команд create_pkg не влияет на результат

Далее добавляя файлы проверяйте, что они executable

Для этого в Properties/permissions ставим галочку около allow executing file as program для каждого конкретного файла


2. После создания пакета заменяем в нём файлы CMAKE и xml и добавляем setup.py

3. Добавляем папку launch и перемещаем туда launch файл нужного алгоритма

4. Добавляем папку scripts и перемещаем в неё необходимые для алгоритма скрипты

5. Добавляем папку src, в неё папку bug_alg в неё переносим файл __init__.py

6. Открываем terminal и пишем команды 

cd ~/catkin_ws/

catkin_make

source devel/setup.bash

5. Иногда возникают проблемы с catkin_make и приходится повторять 6 шаг несколько раз



Средства работы с мирами Газебо
Для миров из папки со средами запуска достаточно будет переместить launch файл в ~/catkin_ws/src/turtlebot3_simulations/turtlebot3_gazebo/launch и заменить <worldname>.world в самом файле на расположение мира газебо у себя в системе

Проверьте, что после скачивание папки адрес dae файла внутри файла world совпадает с расположение соответствующего dae файла в системе

Для этого нам понадобится заранее установленный пакет для работы в gazebo с turtlebot3

1. Заходим в папку ~/catkin_ws/src/turtlebot3_simulations/turtlebot3_gazebo/launch

2. Создаём файл <filename>.launch
 Копируем туда код, заменив <worldname>.world на расположение мира газебо у себя в системе
 
 //
 <launch>
  <arg name="model" default="$(env TURTLEBOT3_MODEL)" doc="model type [burger, waffle, waffle_pi]"/>
  <arg name="x_pos" default="1.5"/>
  <arg name="y_pos" default="1.5"/>
  <arg name="z_pos" default="1.0"/>

  <include file="$(find gazebo_ros)/launch/empty_world.launch">
    <arg name="world_name" value="<worldname>.world"/>
    <arg name="paused" value="false"/>
    <arg name="use_sim_time" value="true"/>
    <arg name="gui" value="true"/>
    <arg name="headless" value="false"/>
    <arg name="debug" value="false"/>
  </include>

  <param name="robot_description" command="$(find xacro)/xacro --inorder $(find turtlebot3_description)/urdf/turtlebot3_$(arg model).urdf.xacro" />

  <node name="spawn_urdf" pkg="gazebo_ros" type="spawn_model" args="-urdf -model turtlebot3 -x $(arg x_pos) -y $(arg y_pos) -z $(arg z_pos) -param robot_description" />
</launch>
//

<arg name="x_pos" default="1.5"/>
<arg name="y_pos" default="1.5"/>
<arg name="z_pos" default="1.0"/>

Изменяя аргументы в этих трёх строчках можно менять координаты спавна робота



ВАЖНО: Проверьте, что после скачивания world файла адрес соответствующего dae файла внутри совпадает с расположением этого же dae файла в системе

3. Откройте терминал и напишите 
export TURTLEBOT3_MODEL=burger

Затем
roslaunch turtlebot3_gazebo <filename>.launch 

После этого загрузится Ваш собственный мир газебо

(ДОБАВИЛ НОВОЕ)
Чтобы не писать каждый раз эти команлды можно написать скрипт на bash'е 
в папке catkin_ws. Название файла "start.bash" 
Код:
catkin_make
source devel/setup.bash
export TURTLEBOT3_MODEL=burger
roslaunch turtlebot3_gazebo turtlebot3_stage_4.launch

Запустить карту 
bash start.bash
(КОНЕЦ)




Запуск алгоритмов

1. Открыть консоль и прописать
roslaunch bug_alg bug1.launch des_x:=6 des_y:=6
или 
roslaunch bug_alg bug2.launch des_x:=6 des_y:=6

в зависимости от желаемого алгоритма

Меняя значения des_x и des_y можно изменять координаты точки, до которой необходмио будет доехать роботу

(ДОБАВИЛ НОВОЕ)
Алгоритм можно запускать с помощью Makefile'а. Makefile должен располагаться в папке catkin_ws
Код:
bug1:
	roslaunch bug_alg bug1.launch des_x:=6 des_y:=6

bug2:
	roslaunch bug_alg bug2.launch des_x:=-1.1 des_y:=-1.1

class1:
	roslaunch bug_alg class1.launch des_x:=2 des_y:=-1

class11:
	roslaunch bug_alg class11.launch des_x:=3 des_y:=4

distbug:
	roslaunch bug_alg distbug.launch des_x:=3 des_y:=0

distbug_step:
	roslaunch bug_alg distbug_step.launch des_x:=3 des_y:=0

Запустить алгоритм:
make {алгоритм}
(КОНЕЦ)




(Доп. инфа по алгоритмам)
Заметил, что баги в начале работы, когда поварачиваются к точке поварачиваютсчя не по оптимальному пути(угол их поворота мог быть больше 180 градусов, например надо было повернуться на угол вправо на 50 градусов, а робот мог повернуться через лево на 310 градусов).
надо было чуть переписать go_to_point.py и часть в багах где робот поварачивается к точке, в bug2.py это строчки 158-165 (исправленные 158-173) 
Код:
while not math.fabs(err_yaw) <= math.pi / 90:
  twist_msg = Twist()
  desired_yaw = math.atan2(desired_position_.y - position_.y, desired_position_.x - position_.x)
  err_yaw = desired_yaw - yaw_
  if math.fabs(err_yaw) > math.pi:
      if err_yaw > 0:
          err_yaw = err_yaw - 2 * math.pi
      else: 
          err_yaw = err_yaw + 2 * math.pi
  if err_yaw > 0:
      twist_msg.angular.z = 0.7
  else: 
      twist_msg.angular.z = -0.7
  pub.publish(twist_msg)
  twist_msg.angular.z = 0
  pub.publish(twist_msg)