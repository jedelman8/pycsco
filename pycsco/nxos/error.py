class CLIError(Exception):
	def __init__(self, err, msg):
		self.err = err
		self.msg = msg

	def __str__(self):
		return self.err + " " + self.msg