====================================================
How to Setup
----------------------------------------------------
1.  put the "rt.py", "t.py", "tp.py" under the same folder.
2.  go to the directory where RYU is installed.
3.  backup the original "simple_switch_13.py".
4.  replace with the provided "simple_switch_13.py".
====================================================
How to Run
----------------------------------------------------
1.  run the ryu-controller, i.e., open a CMD terminal and run this command:
    "ryu-manager rt.py"
2.  the controll interface is automatically pop-up; if closed by accident,
    simply open another CMD terminal, and run "python3 t.py"
3.  run the topology, i.e., open another CMD terminal and run this command:
    "sudo python3 tp.py"
    then wait for the topology and corresponding CLI to load
====================================================
REST API Commands (host 10.0.0.1 as example)
----------------------------------------------------
1.  Ordinary-level list
1.1. view the ordinary list:
    on the control window, click "ordinary list"
    then on the "ord list control" window, click "view"
    see the results in the corresponding CMD terminal
    or equivalently, close the control window and run this command:
    "curl -X GET http://127.0.0.1:8080/simpleswitch/ord_list"

2.  Higher-level list
2.1. view the higher-level list:
    on the control window, click "high list"
    then on the "high list control" window, click "view"
    or
    "curl -X GET http://127.0.0.1:8080/simpleswitch/high_list/0000000000000001"
2.2. POST a host to the higher-level list:
    on the control window, click "high list"
    then on the "high list control" window, click "mod"
    on the "Choose a host" window, choose any host (e.g., "Host 1")
    or
    "curl -X POST -d '{"addr":"10.0.0.1"}' http://127.0.0.1:8080/simpleswitch/high_list/0000000000000001"

3.  Ban-list 
3.1. View the ban-list:
    on the control window, click "ban list"
    then on the "ban list control" window, click "view"
    or
    "curl -X GET http://127.0.0.1:8080/simpleswitch/ban_list/0000000000000001"
3.2. Lift ban of a host:
    on the control window, click "ban list"
    then on the "ban list control" window, click "mod"
    on the "Choose a host" window, choose any host (e.g., "Host 1")
    or
    "curl -X DELETE -d '{"addr":"10.0.0.1"}' http://127.0.0.1:8080/simpleswitch/ban_list/0000000000000001"

4.  Data usage
    on the control window, click "data usage"
    then on the "data usage control" window, click "view"
    or
    "curl -X GET http://127.0.0.1:8080/simpleswitch/data_usage/0000000000000001"

====================================================
Test data rate (host 10.0.0.1 as example)
----------------------------------------------------
1.  on the CLI of Mininet, run this command:
    "xterm h1 h99 h100"
2.  on the "Xterm" window of Host 100 (h100), run this command:
    "iperf -s -i 1"
3.  on the "Xterm" window of Host 99 (99), run this command:
    "iperf -s -i 1"
4.  on the "Xterm" window of Host 1 (h1), run this command:
    "iperf -c 10.0.0.253 -t 5"
    or 
    "iperf -c 10.0.0.254 -t 5"
5.  test Step 4 before and after Host 1 is POST to higher-level list
====================================================