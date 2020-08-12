import torch
import numpy as np
import sys
import matplotlib.pyplot as plt
from network import *
from until import *
# sys.stdout = open("model/loss.txt", "w")

BATCH_SIZE = 128
NUM_LAYERS = 20
EMBEDDING_SIZE = 100
HIDDEN_SIZE = 100
GRAD_CLIP = 1
NUM_EPOCH = 8
USE_CUDA = torch.cuda.is_available()
DEVICE = "cuda" if USE_CUDA else "cpu"


def train_notes():
    if not os.path.exists("data/note/train_note"):
        pure_notes()
    all_notes = read_("data/note/notes")
    note_names = sorted(set(all_notes))
    train_notes_input, train_notes_output = prepare_train_notes()
    val_notes_input, val_notes_output = prepare_val_notes()
    # print("len of train_notes_input:", len(train_notes_input))
    # print("len of val_notes_input", len(val_notes_input))
    print(len(note_names))
    # return 0
    model = ThreeLayerLSTM(len(note_names), EMBEDDING_SIZE, HIDDEN_SIZE, NUM_LAYERS, dropout=0.5)
    if USE_CUDA:
        model = model.cuda()
    loss_fn = torch.nn.CrossEntropyLoss()   
    learning_rate = 0.0001
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, 0.5)
    
    train_loss_list = []
    val_loss_list = []
    countx = 0
    fail_countx = 0
    val_losses = []
    for epoch in range(NUM_EPOCH):
        model.train()
        hidden = model.init_hidden(BATCH_SIZE)
        for start in range(0, len(train_notes_input) - BATCH_SIZE, BATCH_SIZE):
            end = start + BATCH_SIZE
            batchX = torch.LongTensor(train_notes_input[start:end])
            batchY = torch.LongTensor(train_notes_output[start:end])
            if USE_CUDA:
                batchX = batchX.cuda()
                batchY = batchY.cuda()
            hidden = repackage_hidden(hidden)
            model.zero_grad()
            output, hidden = model(batchX, hidden)
            loss = loss_fn(output.view(-1, 10), batchY.view(-1))
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
            optimizer.step()
            print("Epoch :", epoch, loss.item())
            if countx % 100 == 0:
                train_loss_list.append(loss.item())
                val_loss = evaluate(model, loss_fn, val_notes_input, val_notes_output)
                val_loss_list.append(val_loss)
                if len(val_losses) == 0 or val_loss < min(val_losses):
                    print("best_notes_loss :", val_loss)
                    # torch.save(model.state_dict(), "model/notes.pth")
                    val_losses.append(val_loss)
                    fail_countx = 0
                else:
                    fail_countx += 1
                    if fail_countx == 3:
                        scheduler.step()
                        # optimizer = torch.optim.SGD(model.parameters(), learning_rate)
                        fail_countx = 2
            countx += 1
    draw(train_loss_list, val_loss_list)


def repackage_hidden(hidden):
    if isinstance(hidden, torch.Tensor):
        return hidden.detach()
    else:
        return tuple(repackage_hidden(h) for h in hidden)


def evaluate(model, loss_fn, val_notes_input, val_notes_output):
    model.eval()
    total_loss = 0.
    total_count = 0.
    with torch.no_grad():
        hidden = model.init_hidden(BATCH_SIZE, requires_grad=False)
        for start in range(0, len(val_notes_input) - BATCH_SIZE, BATCH_SIZE):
            end = start + BATCH_SIZE
            batchX = torch.LongTensor(val_notes_input[start:end])
            batchY = torch.LongTensor(val_notes_output[start:end])
            if USE_CUDA:
                batchX = batchX.cuda()
                batchY = batchY.cuda()
            hidden = repackage_hidden(hidden)
            with torch.no_grad():
                output, hidden = model(batchX, hidden)
            loss = loss_fn(output.view(-1, 10), batchY.view(-1))
            total_loss = float(loss.item()) * float(len(val_notes_input)) * 10. * float(len(val_notes_output)) * 10.
            total_count = float(len(val_notes_input)) * 10. * float(len(val_notes_output)) * 10.
    loss = total_loss / total_count
    model.train()
    return loss


def draw(train_loss_list, val_loss_list):
    x1 = range(0, len(train_loss_list))
    y1 = train_loss_list
    plt.subplot(2, 1, 1)
    plt.plot(x1, y1, '.-')
    plt.title("note_loss(Adam),Embedding-size=100")
    plt.ylabel("train_loss")
    x2 = range(0, len(val_loss_list))
    y2 = val_loss_list
    plt.subplot(2,1,2)
    plt.plot(x2, y2, 'b--')
    plt.xlabel("BATCH_ID")
    plt.ylabel("val_loss")
    plt.savefig("model/note_loss(Adam)100(1).jpg")
    plt.show()


if __name__ == '__main__':
    train_notes()