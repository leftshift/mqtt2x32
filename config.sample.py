broker = {
	"hostname": "host",
	"port": 1883,
	"user": "user",
	"password": "password"
}

# topic = "mumalab/mccafe/1/buttonpress/"
topic = "mumalab/audio/x32/"

#### x32
volume_increment = 0.05
volume_increment_db = 2

# Paths for the x32:
paths = {
	"volume" : "/dca/1/fader",
}

inputs = {
	"pi" : "/ch/01",
	"line_in" : "/auxin/05",
}

outputs = {
	"b1" : "/mtx/02"
}
