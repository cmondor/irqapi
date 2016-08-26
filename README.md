# Interrupt Details and IRQ Tuning REST API

A prototype library for retrieving interrupt details and for tuning irq channels by pinning them to a specific CPU.

## Usage

#. install and activate python virtual environment

`sudo pip install virtualenv`

`virtualenv venv`

`. venv/bin/activate`

#. install required packages

`pip install -r requirements.txt`

#. run server 

`python app.py`

## API endpoints

### GET http://localhost:8080/irq/v1/interrupt_details?begin_time=2012-04-15T23:23:59&end_time=2015-06-12T23:23:59

success returns HTTP 200 interrupt details, distribution, etc in json

errors return 400 with message in json

### POST 'irq_num=INTEGER&cpu=INTEGER' http://localhost:8080/irq/v1/pin_irq

success returns HTTP 200

errors return HTTP 400 with 'message' in json

## Running as Linux Service

TODO: see init folder

## Requires

#. python 2.x
#. virtualenv

## License

The cm_irq library is open-sourced software licensed under the [MIT license](http://opensource.org/licenses/MIT).