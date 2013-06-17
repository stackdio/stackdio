var http = require('http')
    ,connect = require('connect')
    ,options = {}
    ,server
    ;

console.log(__dirname + '/../src');

var app = connect()
  .use(connect.logger('dev'))
  .use(connect.static(__dirname + '/../src'));


http.createServer(app).listen(3000);
