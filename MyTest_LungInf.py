import torch
import torch.nn.functional as F
import numpy as np
import os, argparse
from scipy import misc
from Code.model_lung_infection.InfNet_Res2Net import PraNetPlusPlus as Network
from Code.utils.dataloader_LungInf import test_dataset

parser = argparse.ArgumentParser()
parser.add_argument('--testsize', type=int, default=352, help='testing size')
parser.add_argument('--data_path', type=str, default='./Dataset/TestingSet/LungInfection-Test/',
                    help='Path to test data')
parser.add_argument('--pth_path', type=str, default='./Snapshots/save_weights/Semi-Inf-Net/Semi-Inf-Net-100.pth',
                    help='Path to weights fileif `semi-sup`, edit it to `Semi-Inf-Net/Semi-Inf-Net-100.pth`')
parser.add_argument('--save_path', type=str, default='./Results/Lung infection segmentation/Semi-Inf-Net/',
                    help='Path to save the predictions. if `semi-sup`, edit it to `Semi-Inf-Net`')
opt = parser.parse_args()

model = Network()
# model = torch.nn.DataParallel(model, device_ids=[0, 1])
model.load_state_dict(torch.load(opt.pth_path))
model.cuda()
model.eval()

image_root = '{}/Imgs/'.format(opt.data_path)
gt_root = '{}/GT/'.format(opt.data_path)
test_loader = test_dataset(image_root, gt_root, opt.testsize)
os.makedirs(opt.save_path, exist_ok=True)

for i in range(test_loader.size):
    image, gt, name = test_loader.load_data()
    gt = np.asarray(gt, np.float32)
    gt /= (gt.max() + 1e-8)
    image = image.cuda()

    lateral_map_5, lateral_map_4, lateral_map_3, lateral_map_2, lateral_edge = model(image)
    res = lateral_map_2
    res = F.upsample(res, size=gt.shape, mode='bilinear', align_corners=False)
    res = res.sigmoid().data.cpu().numpy().squeeze()
    res = (res - res.min()) / (res.max() - res.min() + 1e-8)
    misc.imsave(opt.save_path+name, res)


# NOTES: calculate fps
# model_lung_infection = PraNet().cuda().eval()
# input_tensor = torch.randn(1, 3, 352, 352).cuda()
# flops, params = profile(model_lung_infection, inputs=(input_tensor,))
# flops, params = clever_format([flops, params], "%.3f")
# print(flops, params)
#
#
# t_total = 0
#
# for i in range(1000):
#     start = time.time()
#     res, _, _, _ = model_lung_infection(input_tensor)
#     t_cur = time.time() - start
#     print('[cur Time] {}, [cur FPS] {}'.format(t_cur, 1 / t_cur))
#     t_total += t_cur
#
# print('[time] {} [FPS] {}'.format(t_total/1000, 1000/t_total))