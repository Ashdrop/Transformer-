import os
import torch
import torch.nn as nn
from transformers import BertTokenizer, AdamW, BertConfig
from torch.utils.data import DataLoader
from model import BertClassifier
from dataset import CNewsDataset
from tqdm import tqdm

def main():

    batch_size = 4
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    epochs = 10
    learning_rate = 5e-6    

    train_dataset = CNewsDataset('data/cnews/cnews.train.txt')
    valid_dataset = CNewsDataset('data/cnews/cnews.val.txt')
    #test_dataset = CNewsDataset('data/cnews/cnews.test.txt')


    # train_dataloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    valid_dataloader = DataLoader(valid_dataset, batch_size=batch_size, shuffle=False)
    #test_dataloader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    bert_config = BertConfig.from_pretrained('bert-base-chinese')
    num_labels = len(train_dataset.labels)

    model = BertClassifier(bert_config, num_labels).to(device)

    optimizer = AdamW(model.parameters(), lr=learning_rate)
    criterion = nn.CrossEntropyLoss()

    best_acc = 0

    for epoch in range(1, epochs+1):
        losses = 0      # 损失
        accuracy = 0    # 准确率

        model.train()
        train_dataloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        train_bar = tqdm(train_dataloader, ncols=100)
        for input_ids, token_type_ids, attention_mask, label_id in train_bar:
            model.zero_grad()
            train_bar.set_description('Epoch %i train' % epoch)

            output = model(
                input_ids=input_ids.to(device), 
                attention_mask=attention_mask.to(device), 
                token_type_ids=token_type_ids.to(device), 
            )

            loss = criterion(output, label_id.to(device))
            losses += loss.item()

            pred_labels = torch.argmax(output, dim=1)   # 预测出的label
            acc = torch.sum(pred_labels == label_id.to(device)).item() / len(pred_labels) #acc
            accuracy += acc


            loss.backward()
            optimizer.step()
            train_bar.set_postfix(loss=loss.item(), acc=acc)


        average_loss = losses / len(train_dataloader)
        average_acc = accuracy / len(train_dataloader)

        print('\tTrain ACC:', average_acc, '\tLoss:', average_loss)

        model.eval()
        losses = 0      
        accuracy = 0    
        valid_bar = tqdm(valid_dataloader, ncols=100)
        for input_ids, token_type_ids, attention_mask, label_id  in valid_bar:
            valid_bar.set_description('Epoch %i valid' % epoch)

            output = model(
                input_ids=input_ids.to(device), 
                attention_mask=attention_mask.to(device), 
                token_type_ids=token_type_ids.to(device), 
            )
            
            loss = criterion(output, label_id.to(device))
            losses += loss.item()

            pred_labels = torch.argmax(output, dim=1)   # 预测出的label
            acc = torch.sum(pred_labels == label_id.to(device)).item() / len(pred_labels) #acc
            accuracy += acc
            valid_bar.set_postfix(loss=loss.item(), acc=acc)

        average_loss = losses / len(valid_dataloader)
        average_acc = accuracy / len(valid_dataloader)

        print('\tValid ACC:', average_acc, '\tLoss:', average_loss)

        if not os.path.exists('models'):
            os.makedirs('models')
        
        if average_acc > best_acc:
            best_acc = average_acc
            torch.save(model.state_dict(), 'models/best_model.pkl')
        
if __name__ == '__main__':
    main()