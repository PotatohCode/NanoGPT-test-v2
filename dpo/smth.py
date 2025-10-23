def generate_math_qns():
    a = random.choice(list(range(0,100)) + ['x'] * 10)
    b = random.choice(range(0,100) if a == 'x' else list(range(0,100)) + ['x'] * 10)
    op = random.choice(['+', '-', '*'])
    if a == 'x' or b == 'x':
        result = random.randint(0, 99)
        return f"{a}{op}{b}={result}, x=? "
    else:
        return f"{a}{op}{b}=? "

def generate_positive_ollama(prompt, example):
    system_prompt = f"""
        You are an AI that generates math reasoning examples.
        Respond strictly in the format:
        <question> The answer is <answer> because <working> equals <answer>

        Rules:
        - Only give the most simplified working
        - Round decimals to 3dp
        - Answer strictly in the given format
        - The working should be short in the exact format of <x> <operation> <y>
        - Repeat the question at the start of every response

        Examples:
        {example}
    """
    response = ollama.chat(
        model='llama3.2:3b',  # or another local model
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt}
        ]
    )
    return response['message']['content'].strip()

# complile examples from json
example = ''
with open("pos_neg_pairs.json", "r+", encoding="utf-8") as f:
    data = json.load(f)

    for line in data:
        example += line['positive'] + '\n'
    
    # generate neg pos pair
    for i in range(100000):
        prompt = generate_math_qns()
        correct = False
        while(not correct): # repeatedly generate pos till correct output generates
            positive = generate_positive_ollama(prompt, example)
            if any(s in positive for s in ['<', '>', 'operation', '\n']) or len(positive) > 100:
                continue
            else:
                correct = True

        correct = False
        while(not correct): # repeatedly generate neg till correct output generates
            input_ids = torch.tensor([encode(prompt)], dtype=torch.long, device=device)
            output = gpt.generate(
                input_ids,
                max_new_tokens=max_new_tokens,      # how many tokens to generate
                temperature=0.1,        # higher = more random
                top_k=200               # sample from top 200 candidates
            )

            negative = decode(output[0][0].tolist())
            if negative.split('? ')[1] == "Sorry, I don't know.":
                correct = True
                pair = {"negative" : negative, "positive" : positive}
                data.append(pair)
    f.seek(0)
    json.dump(data, f)
    print('Completed')