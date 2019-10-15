import dns.resolver

answers = dns.resolver.query('www.sina.com.cn', 'A', tcp=False)
for i in answers.response.answer:
    for j in i.items:
        print(j)

answers_wTCP = dns.resolver.query('www.sina.com.cn', 'A', tcp=True)
for i in answers_wTCP.response.answer:
    for j in i.items:
        print(j)
