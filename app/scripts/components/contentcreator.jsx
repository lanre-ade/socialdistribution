import React from 'react';
import Reflux from 'reflux';
import Moment from 'moment';
import { Link } from 'react-router';
import { Input } from 'react-bootstrap';
import { markdown as Markdown } from 'markdown';

import PostActions from '../actions/post';

// Responsible for creating posts/comments and notifying the Post store when
// this happens.
export default React.createClass({

  getInitialState: function() {
    return this.defaultContent();
  },

  defaultContent: function () {
    return {
      format: "markdown",
      content: ""
    };
  },

  formatChange: function(event) {
    this.setState({format: event.target.value});
  },

  contentChange: function(event) {
    this.setState({content: event.target.value});
  },

  submitContent: function() {

    // capture the current content in our inputs
    var content = {
      author: this.props.currentAuthor,
      content: this.state.content,
      type: this.state.format,
      timestamp: Moment.unix()
    };

    // reset content state now that we have it stored
    this.setState(this.getInitialState());

    // populate content with appropriate metadata
    if (this.props.forComment) {
      PostActions.newComment(this.props.post, content);
    } else {
      content.comments = [];
      PostActions.newPost(content);
    }
  },

  render: function() {
    var Submit = <Input className="pull-right" type="submit" value="Post" onClick={this.submitContent} />;
    return (
      <div className="media">
        <div className="media-left">
          <Link to="author" params={{id: this.props.currentAuthor.id}}>
            <img className="media-object author-image" src={this.props.currentAuthor.image}/>
          </Link>
        </div>
        <div className="media-body content-creator">
          <Input type="textarea" placeholder="Say something witty..." value={this.state.content} onChange={this.contentChange} />
          <Input type="select" value={this.state.format} onChange={this.formatChange} buttonAfter={Submit}>
            <option value="markdown">Markdown</option>
            <option value="text">Text</option>
          </Input>
        </div>
      </div>
    );
  }
});
