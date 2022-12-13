from jetson.inference import detectNet
import jetson.utils
net = detectNet("ssd-mobilenet-v2", threshold=0.5)
