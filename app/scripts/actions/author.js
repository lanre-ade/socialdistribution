import Reflux from 'reflux';
import Request from '../utils/request';

var Author = Reflux.createActions({
  'update': {},
  'register': { asyncResult: true},
  'logout': {},
  'login': { asyncResult: true},
  'getAuthorNameList': {},
  'checkAuth': {},
  'getAuthorViewData': {}
});

Author.login.listen(function(username, password) {
  Request
    .get('http://localhost:8000/author/login/') //TODO: remove host
    .auth(username, password)
    .promise()
    .then( this.completed )
    .catch( this.failed );
} );

export default Author;
