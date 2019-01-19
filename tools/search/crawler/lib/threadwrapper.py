from multiprocessing import Process


# Wrap a method call in a different process, so that we can process
# keyboard interrupts and actually terminate it if we have to.
# python threading makes it often impossible to Ctlr-C it otherwise..
#
# NOTE! Database connections and similar objects must be instantiated
# in the subprocess, and not in the master, to be fully safe!
def threadwrapper(func, *args):
    p = Process(target=func, args=args)
    p.start()

    # Wait for the child to exit, or if an interrupt signal is delivered,
    # forcibly terminate the child.
    try:
        p.join()
    except KeyboardInterrupt as e:
        print("Keyboard interrupt, terminating child process!")
        p.terminate()
    except Exception as e:
        print("Exception %s, terminating child process!" % e)
        p.terminate()
