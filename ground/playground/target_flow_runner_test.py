__author__ = 'Ori'

from AUVSIground.auto_detect.classification_runners import TargetFlowRunner

flow_runner = TargetFlowRunner(r"C:\Users\Ori\ftp_playground\crops")
while True:
    flow_res = flow_runner.classify_one_crop()

    print(flow_res)