#!/bin/env bash

curl -s http://192.168.195.100:8080/irq/v1/interrupt_details

curl -s -d 'irq_num=132&cpu=1' -XPOST http://192.168.195.100:8080/irq/v1/pin_irq