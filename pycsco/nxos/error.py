class CLIError(Exception):
    def __init__(self, err, msg, index):
        self.err = err
        self.msg = msg
        self.index = index

    def __str__(self):
        return '''NX-OS CLI Configuration Error\n {err}. {message}. \
                Error Found on Command Number: {number}'''.format(
                        err     = self.err,
                        message = self.msg,
                        number  = (self.index + 1)
                )


class InputError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return 'Invalid Input Error\n' + self.msg

class FileTransferError(Exception):
    pass

class DiffError(Exception):
    pass