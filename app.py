
# Toxic Comment detection......................................................................................

from flask import Flask, request, render_template
import pandas as pd
import re
import torch
from transformers import RobertaTokenizer, RobertaForSequenceClassification
from transformers import Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from torch.utils.data import Dataset

app = Flask(__name__)

# Load the dataset
data = pd.read_csv("toxic.csv")
data = data.drop("Unnamed: 0", axis=1)

# Text preprocessing function
def prepare_text(text):
    text = re.sub(r'[^a-zA-Z]', ' ', text)
    text = text.lower()
    return text

data['clean_tweets'] = data['tweet'].apply(lambda x: prepare_text(x))

# Create a custom dataset class
class ToxicCommentDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, item):
        text = self.texts[item]
        label = self.labels[item]

        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            return_token_type_ids=False,
            padding='max_length',
            return_attention_mask=True,
            return_tensors='pt',
            truncation=True,
        )

        return {
            'text': text,
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

# Split the data
train_texts, test_texts, train_labels, test_labels = train_test_split(
    data['clean_tweets'], data['Toxicity'], test_size=0.2, random_state=42
)

# Load the RoBERTa tokenizer
tokenizer = RobertaTokenizer.from_pretrained('roberta-base')

# Create datasets
train_dataset = ToxicCommentDataset(
    texts=train_texts.to_list(),
    labels=train_labels.to_list(),
    tokenizer=tokenizer,
    max_len=128
)

test_dataset = ToxicCommentDataset(
    texts=test_texts.to_list(),
    labels=test_labels.to_list(),
    tokenizer=tokenizer,
    max_len=128
)

# Load the RoBERTa model
model = RobertaForSequenceClassification.from_pretrained('roberta-base', num_labels=2)

# Training arguments
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir='./logs',
    logging_steps=10,
    evaluation_strategy="epoch",
)

# Metrics function
def compute_metrics(p):
    preds = p.predictions.argmax(-1)
    precision, recall, f1, _ = precision_recall_fscore_support(p.label_ids, preds, average='binary')
    acc = accuracy_score(p.label_ids, preds)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    compute_metrics=compute_metrics
)

# Train the model
trainer.train()

# Evaluate the model
eval_result = trainer.evaluate()

print(f"Accuracy: {eval_result['eval_accuracy']}")
print(f"F1 Score: {eval_result['eval_f1']}")
print(f"Precision: {eval_result['eval_precision']}")
print(f"Recall: {eval_result['eval_recall']}")

# Save the model and tokenizer
model.save_pretrained('./model')
tokenizer.save_pretrained('./model')

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    comment = request.form['comment']
    clean_comment = prepare_text(comment)
    
    encoding = tokenizer.encode_plus(
        clean_comment,
        add_special_tokens=True,
        max_length=128,
        return_token_type_ids=False,
        padding='max_length',
        return_attention_mask=True,
        return_tensors='pt',
        truncation=True,
    )

    input_ids = encoding['input_ids']
    attention_mask = encoding['attention_mask']

    output = model(input_ids, attention_mask=attention_mask)
    _, prediction = torch.max(output.logits, dim=1)

    result = "Toxic" if prediction == 1 else "Not Toxic"
    return f"Comment: {comment}<br>Prediction: {result}"

if __name__ == '__main__':
    app.run(debug=True)
