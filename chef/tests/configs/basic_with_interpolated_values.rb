key_name = 'client'
chef_server_url "#{url}"
client_key "../#{key_name}.pem"
# Use both kind of quotes, also a comment for testing
node_name "test_1"
# test multiple line values
client_name = {
    'dev' =>'test_1'
}['dev']
