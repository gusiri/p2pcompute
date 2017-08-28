# p2pcompute
Steps to use this project:

1. Make sure the database is up and running and has the table with respective rows in it. You can create a new database and name the same in the project in Tracker.py

2. It will automatically create table if a new line as db.create_table() is written in the code

3. Run Tracker.py forever on a specific machine so that it can serve the requests. Following is the example command ot run Tracker:
python Tracker.py

4. Next, run the compute clients on as many nodes you want with different roles. You can run a client either as a requestor or a provider. Following are the commands to run the compute client:
sudo python ComputeClient.py --type=provider --memory=100
sudo python ComputeClient.py --type=requestor --memory=100

5. The above commands spawn the clients as requestor and provider. Provider is willing to provide 100m memory and requestor wants 100m from each provider. In this project, the no of peers reqeustor asks for is fixed i.e 3. 

6. Before running this project, make sure to install python and ethereum. This project uses ethereum for its payment system.
