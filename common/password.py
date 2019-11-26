import hmac
from hashlib import md5

# message = b"55005"
# key = b"123456"

message = b"123456"
key = b"55005"

h = hmac.new(key, message, digestmod="MD5")
result = h.hexdigest()
#a3aa6035b15bb6ea4041a939c315914a
print(result)
