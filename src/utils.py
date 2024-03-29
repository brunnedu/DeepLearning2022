import os
import logging
import time
import csv
import random
import numpy as np
import torch
import torch.nn as nn
import torchvision
from matplotlib import pyplot as plt
from torch.optim import Optimizer

from typing import Tuple, Union, List, Dict

from torchvision.transforms import Normalize


def fix_all_seeds(seed: int) -> None:
    """ 
    Fix all the different seeds for reproducibility. 
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed) 

    
def create_logger(experiment_id: str) -> logging.Logger:
    """ 
    Set up a logger for the current experiment.
    """
    # set up directory for the current experiment
    experiment_dir = os.path.join("out", experiment_id)
    log_dir = os.path.join(experiment_dir, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # define filename for log file
    time_str = time.strftime('%Y-%m-%d-%H-%M')
    log_fn = os.path.join(log_dir, f"{time_str}.log")
    
    # set up logger
    logging.basicConfig(filename=str(log_fn), format="%(asctime)-15s %(message)s")
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # only add a stream handler if there isn't already one
    if len(logger.handlers) == 1: # <-- file handler is the existing handler
        console = logging.StreamHandler()
        logger.addHandler(console)

    return logger


def save_plotting_data(experiment_id: str, metric: str, epoch: int, metric_val: float):
    """ 
    Save metrics after each epoch in a CSV file (to create plots for our report later). 
    """
    fn = os.path.join("out", experiment_id, f"{metric}.csv")

    # define header if file does not exist yet
    if not os.path.isfile(fn):
        with open(fn, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["epoch", metric])

    # append new data row
    with open(fn, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([epoch, metric_val])


def save_checkpoint(
    experiment_id: str, 
    next_epoch: int,
    best_acc: float,
    model: nn.Module,
    optimizer: Optimizer,
    filename: str="checkpoint.pth.tar"
    ):
    """
    Save all the necessary data to resume the training at a later point in time.
    More details: https://pytorch.org/tutorials/recipes/recipes/saving_and_loading_a_general_checkpoint.html 
    """
    # checkpoint states
    d = {
        "next_epoch": next_epoch,
        "best_acc": best_acc,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
    }

    experiment_dir = os.path.join("out", experiment_id)
    torch.save(d, os.path.join(experiment_dir, filename))


def load_checkpoint(experiment_id: str, model: nn.Module, optimizer: Optimizer) -> Tuple[nn.Module, Optimizer, int, float]:
    """ 
    Load the latest checkpoint and return the updated model and optimizer, the next epoch and best accuracy so far. 
    """
    # load checkpoint
    filename = os.path.join("out", experiment_id, "checkpoint.pth.tar")
    checkpoint = torch.load(filename)

    # restore model and optimizer state
    model.load_state_dict(checkpoint['model_state_dict']) 
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

    next_epoch = checkpoint['next_epoch']
    best_acc = checkpoint['best_acc']

    return model, optimizer, next_epoch, best_acc


def load_best_model(experiment_id: str, model: nn.Module) -> nn.Module:
    """
    Load the model weights that resulted in the highest validation accuracy in a previous experiment.
    """
    # load best model
    filename = os.path.join("out", experiment_id, "best_model.pth.tar")
    model_state_dict = torch.load(filename, map_location=torch.device("cuda" if torch.cuda.is_available() else "cpu"))
    model.load_state_dict(model_state_dict)

    return model


def save_model(model: nn.Module, experiment_id: str, filename: str):
    """
    Save the current model from the current experiment.
    """
    experiment_dir = os.path.join("out", experiment_id)
    torch.save(model.state_dict(), os.path.join(experiment_dir, filename))


def display_image(
        image: Union[torch.Tensor, List[torch.Tensor]],
        normalization_params: Dict = None,
        plt_title: str = None,
        nrow: int = 8,
):
    """ 
    Display a single or multiple torch.Tensor images.
    """
    if not (isinstance(image, torch.Tensor) and len(image.shape) == 3):
        # place images into grid
        image = torchvision.utils.make_grid(image, nrow=nrow)

    if normalization_params is not None:
        # reverse normalization according to normalization dict
        norm_mean, norm_std = np.array(normalization_params['mean']), np.array(normalization_params['std'])
        reverse_normalize = Normalize(mean=-norm_mean / norm_std, std=1 / norm_std)
        image = reverse_normalize(image)

    img_np = image.numpy()
    # shuffle the color channels correctly
    plt.imshow(np.transpose(img_np, (1, 2, 0)))

    # plot
    plt.title(plt_title)
    plt.show()


def display_dataset_sample(ds_sample: Tuple[torch.Tensor, torch.Tensor], normalization_params=None):
    """
    Display a single or multiple torch.Tensor images with the corresponding labels.
    """
    features, labels = ds_sample
    display_image(list(features), normalization_params=normalization_params, plt_title=f"label: {labels.item() if isinstance(labels, torch.Tensor) else labels}")
