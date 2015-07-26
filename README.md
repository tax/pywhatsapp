# Example usage
You can register a whatsapp client with the yowsup-cli ([see registration](https://github.com/tgalal/yowsup/wiki/yowsup-cli-2.0))

```python
from whatsapp import Client

to = '31641371199'

client = Client(login='3161516888', password='secretpasswordbase64')
client.send_message(to, 'Hello lola')
client.send_media(to, path='/Users/tax/Desktop/logo.jpg')
```

# Installation
```
$ pip install pywhatsapp
```