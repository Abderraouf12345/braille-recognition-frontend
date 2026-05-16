import os
import torch
import torch.nn as nn

class DotPredictor(nn.Module):
    def __init__(self):
        super(DotPredictor, self).__init__()
        self.conv_layers = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128), nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        self.fc_layers = nn.Sequential(
            nn.Linear(128, 64), nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        x = self.conv_layers(x)
        x = x.view(x.size(0), -1)
        return self.fc_layers(x)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_3ch = DotPredictor().to(device)
model_path = os.path.join(os.path.dirname(__file__), "..", "..", "best_braille_model_3_channel_augmented.pth")

def load_model():
    if os.path.exists(model_path):
        model_3ch.load_state_dict(torch.load(model_path, map_location=device))
        model_3ch.eval()
        print(f"✅ Model loaded successfully.")
    else:
        print(f"❌ Model file not found at {model_path}.")
    return model_3ch, device
