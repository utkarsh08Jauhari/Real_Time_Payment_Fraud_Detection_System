#ZooKeeper Start
bin\windows\zookeeper-server-start.bat config\zookeeper.properties

#Kafka Server Start
bin\windows\kafka-server-start.bat config\server.properties

#Kafka Topic Creation
bin\windows\kafka-topics.bat --create --topic topic_name --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

#Kafka Producer
bin\windows\kafka-console-producer.bat --topic topic_name --bootstrap-server localhost:9092

#Kafka Consumer
bin\windows\kafka-console-consumer.bat --topic topic_name --from-beginning --bootstrap-server localhost:9092
