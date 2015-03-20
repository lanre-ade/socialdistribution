import _ from 'lodash';
import React from 'react';
import Reflux from 'reflux';
import Moment from 'moment';
import { Link } from 'react-router';
import { markdown as Markdown } from 'markdown';
import { Col } from 'react-bootstrap';

// Represents an individual comment or post.
var Content = React.createClass({

  statics: {
    imgStyle: {
      width: '64px',
      height: '64px'
    },

    convertMarkdown: function(markdown) {
      return Markdown.toHTML(markdown);
    }
  },

  render: function() {
    var content, comments, title;

    if (_.isUndefined(this.props.data)) {
      return (<i className="fa fa-refresh fa-spin fa-5x"></i>);
    }

    if (this.props.data.getType() === "Post") {
      title = this.props.data.title;
      if (this.props.data.hasComments()) {
        comments = this.props.data.getComments().map(function (comment) {
          return (
            <Content key={"comment-"+comment.guid} data={comment} />
          );
        });
      }
    }

    switch(this.props.data.contentType) {
      case 'text/x-markdown':
        content = <div dangerouslySetInnerHTML={{__html: Content.convertMarkdown(this.props.data.content)}} />;
        break;
      case 'text/html':
        content = <div dangerouslySetInnerHTML={{__html: this.props.data.content}} />;
        break;
      default:
        content = <p>{this.props.data.content}</p>;
    }

    // creates those nice "25 minutes ago" timestamps
    var timeSince = Moment.unix(this.props.data.pubDate).fromNow();

    return (
      <div className="media">
        <div className="media-left">
          <Link to="author" params={{id: this.props.data.author.id}}>
            <img className="media-object" src={this.props.data.author.getImage()} style={Content.imgStyle} />
          </Link>
        </div>
        <div className="media-body">
          <Link to="author" params={{id: this.props.data.author.id}}>
            <h4 className="media-heading">{this.props.data.author.name}</h4>
          </Link>
          <h4>{title}</h4>
          {content}
          <h6 className="timestamp">{timeSince}</h6>
          {comments}
        </div>
      </div>
    );
  }
});

export default Content;