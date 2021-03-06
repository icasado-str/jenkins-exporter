#!/usr/bin/env bash

if [ $JENKINS_SERVER ] 
then
    sed -i "s~http://jenkins_server:8080~$JENKINS_SERVER~g" config.ini
fi

if [ $JENKINS_USERNAME ]
then
    sed -i "s/username/$JENKINS_USERNAME/g" config.ini
fi

if [ $JENKINS_PASSWORD ]
then
    sed -i "s/password/$JENKINS_PASSWORD/g" config.ini
fi

/usr/local/bin/python main.py