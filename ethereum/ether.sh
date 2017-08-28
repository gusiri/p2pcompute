#!/bin/bash
#sudo apt-get install software-properties-common python-software-properties
#sudo add-apt-repository -y ppa:ethereum/ethereum
#sudo apt-get update
#sudo apt-get install ethereum
mkfifo pipe
rm -rf miner
geth --datadir miner init genesis.json
geth --datadir miner account new
geth --datadir miner account new
geth --datadir miner account list
echo "" > password.sec
nohup geth --identity "miner" --networkid 1999 --datadir miner --rpc --rpcport "8042" --port "30303" --unlock 0 --password password.sec --ipcpath "~/ethereum/geth.ipc" --mine &
sleep 10
geth attach ~/ethereum/geth.ipc < pipe > data.txt &
TASK_PID=$!
sleep 2
echo "admin.nodeInfo" > pipe
echo "eth.accounts[1]" > pipe
sleep 2
kill $TASK_PID
rm pipe
tail -2 data.txt > temp.txt
head -1 temp.txt > accountno.txt
