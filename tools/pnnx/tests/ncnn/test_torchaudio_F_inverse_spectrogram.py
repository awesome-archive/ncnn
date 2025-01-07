# Tencent is pleased to support the open source community by making ncnn available.
#
# Copyright (C) 2024 THL A29 Limited, a Tencent company. All rights reserved.
#
# Licensed under the BSD 3-Clause License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
# https://opensource.org/licenses/BSD-3-Clause
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchaudio
from packaging import version

class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()

    def forward(self, x, y, z, w):
        x = torch.view_as_complex(x)
        y = torch.view_as_complex(y)
        z = torch.view_as_complex(z)
        w = torch.view_as_complex(w)
        out0 = torchaudio.functional.inverse_spectrogram(x, n_fft=64, window=torch.hann_window(44), win_length=44, hop_length=16, pad=0, center=True, normalized='window', length=None)
        out1 = torchaudio.functional.inverse_spectrogram(y, n_fft=128, window=torch.hann_window(128), win_length=128, hop_length=3, pad=0, center=True, onesided=True, normalized=False, length=None)
        out2 = torchaudio.functional.inverse_spectrogram(z, n_fft=512, window=torch.hamming_window(256), win_length=256, hop_length=128, pad=0, center=True, onesided=True, normalized='frame_length', length=None)
        out3 = torchaudio.functional.inverse_spectrogram(w, n_fft=1024, window=torch.hamming_window(512), win_length=512, hop_length=128, pad=0, center=True, onesided=True, normalized=False, length=None)
        return out0, out1, out2, out3

def test():
    if version.parse(torchaudio.__version__) < version.parse('0.10.0'):
        return True

    net = Model()
    net.eval()

    torch.manual_seed(0)
    x = torch.rand(33, 161, 2)
    y = torch.rand(65, 77, 2)
    z = torch.rand(257, 8, 2)
    w = torch.rand(513, 4, 2)

    a = net(x, y, z, w)

    # export torchscript
    mod = torch.jit.trace(net, (x, y, z, w))
    mod.save("test_torchaudio_F_inverse_spectrogram.pt")

    # torchscript to pnnx
    import os
    os.system("../../src/pnnx test_torchaudio_F_inverse_spectrogram.pt inputshape=[33,161,2],[65,77,2],[257,8,2],[513,4,2]")

    # ncnn inference
    import test_torchaudio_F_inverse_spectrogram_ncnn
    b = test_torchaudio_F_inverse_spectrogram_ncnn.test_inference()

    for a0, b0 in zip(a, b):
        if not torch.allclose(a0, b0, 1e-3, 1e-3):
            return False
    return True

if __name__ == "__main__":
    if test():
        exit(0)
    else:
        exit(1)