# Fetching data from GitHub using REST and GraphQL APIs

With millions of users and public repositories, GitHub is currently the
biggest OpenSource platform in the world. It gathers an unbelievable
amount of projects written in any programming language by people from
all over the world, who contributes to works available for the community.

Did you ever wonder who was the *biggest* contributors of
GitHub, or what was the *most famous* projects available
on the platform, or which users and projects have the biggest influence
on the world wide OpenSource community?

Personally, I do. :wink: And we will try to discover it together.

## Fetching data

To be able to *analyze* GitHub data, we obviously need to
*obtain* GitHub data first! Even if, as for most websites,
all the data that you want is publicly available directly from your
personal navigator, obtaining <strong>all</strong> those data directly
on your system to be able to work on it can actually be quite tricky.

But GitHub (as many other services) offers to us not only one, but two
wonderful open APIs to kindly give us all what we want!
(or at least, nearly all what we want... We'll discuss it later.)
* a good old REST API (<a href="https://developer.github.com/v3/">GitHub API v3</a>) </li>
* a more modern GraphQL API (<a href="https://developer.github.com/v4/">GitHub API v4</a>) </li>

It seems that we are already facing a choice there... and what a choice.

I think that as many developers who know a bit of REST APIs mechanism,
when we discover the theory behind GraphQL APIs, we could think that
GraphQL will revolutionize the Internet and that we can immediately
forget those creepy REST APIs that require us to make millions of
calls to fetch data that we actually do not need.

Theoretically, that could be true, but as usual a trade-off has to
be done between efficiency and simplicity, because actually using
GraphQL complicates a lot both server architectures and queries
design.

So there I will discuss and show examples with the two APIs, because
actually it will be hard to definitively answer on which API is
_currently_ the best.

### Using the REST API

The principle of REST APIs is that you will fetch objects or list of
objects describing what you want through the path of the request on
which you will perform a GET.

However, what you can query obviously depend on the API
implementation. So, let's see direcly in the <a href="https://developer.github.com/v3/">GitHub API documentation</a>
what would be useful for our objective : building a GitHub repositories
and users graph.

Browsing the [repositories API documentation](https://developer.github.com/v3/repos/)
, you will quickly discover that there is an entry to
<a href="https://developer.github.com/v3/repos/#list-all-public-repositories">list all public repositories</a>!
Wonderful, huh? :smirk:

So, let's try this. Event if you can perform GET requests using your
          navigator, personally I prefer using softwares such as
          <a href="https://www.getpostman.com/">PostMan</a>, that allow you
          perform and save any type of request.
          So, the response to a get request on https://api.github.com/repositories should look like this:

```json
[
  {
    "id": 1,
    "node_id": "MDEwOlJlcG9zaXRvcnkx",
    "name": "grit",
    "full_name": "mojombo/grit",
    "private": false,
    "owner": {
      "login": "mojombo",
      "id": 1,
      "node_id": "MDQ6VXNlcjE=",
      "avatar_url": "https://avatars0.githubusercontent.com/u/1?v=4",
      [other_fields]
      },
    "html_url": "https://github.com/mojombo/grit",
    "description": "**Grit is no longer maintained. Check out libgit2/rugged.** Grit gives you object oriented read/write access to Git repositories via Ruby.",
    "fork": false,
    "url": "https://api.github.com/repos/mojombo/grit",
    "forks_url": "https://api.github.com/repos/mojombo/grit/forks",
    "keys_url": "https://api.github.com/repos/mojombo/grit/keys{/key_id}",
    [other_fields]
  },
  {
    [other_repositories]
  }
]
```

As you can see, you will get <strong>lots of data</strong> using REST
API, with a lot of fields that you don't need. Here, we'll only use
two of them for each repository :

* "id"
* "full_name"

And that's all!

Also, you obviously won't get all the data of the 50 millions GitHub
repositories with one query. Actually data for 100 repositories are
received at each call, and you can iterate over repositories setting
up the `page=[last_id_fetched]` of the HTTP request.

Finally, looking again at the <a href="https://developer.github.com/v3/"> GitHub API documentation</a>,
we can see that there is an entry to <a href="https://developer.github.com/v3/repos/#list-contributors">get all contributors</a>
of a given repository, and as with repositories data, we extract the id,
the name, and the number of contributions to the given repository for
each user.

Notice that you will need to do <strong>ONE HTTP REQUEST</strong>
by repository to get its collaborators, what takes a lot of time, even
once automatized using Python for example...

### Using the GraphQL API
#### GitHub GraphQL API basics

So now let's have a look at the GraphQL API.
          
The working principle of those queries is quite different, and a bit
more complicated. Basically, you have a single entry point to the API
(all our requests will be done on https://api.github.com/graphql)
thanks to a *POST request* this time, that contains a
GraphQL request in its body. Then, the server will resolve this query
and send back to you *only what you asked for*, what is
the main interest of those APIs.

If you want an other great use case of what can be done using the
GitHub GraphQL API, I advice you to have a look at
<a href="https://medium.com/@fabiomolinar/using-githubs-graphql-to-retrieve-a-list-of-repositories-their-commits-and-some-other-stuff-ce2f73432f7">this wonderful article</a>
on which I based a part of my work, from Fábio Molinar, who explains
perfectly the interests of GraphQL and its usage for beginners.

Now let's see what we can do in our case. Digging <small>(quite deeply)</small>
into the <a href="https://developer.github.com/v4/">GitHub GraphQL API documentation</a>
you will see that we <em>could</em> build our graph thanks to different approaches.

In the <a href="https://developer.github.com/v4/object/repository/">repository object documentation</a>,
we learn that each <code>repository</code> has a <code>collaborators</code>
<em>connection</em>, but there is no entry to check <em>contributors</em>,
what is slightly different.
Actually, that's no big deal, and we could use collaborators to build
our graph... however, I discovered trying this that you need to be
yourself a collaborator of the considered repository to get its
collaborators... so this approach seems to be a dead end.

However, the <a href="https://developer.github.com/v4/object/user/">user object documentation</a>
presents a <code>repositoriesContributedTo</code> connection, that we
can use to fetch what we want! So let's concretely see how to achieve
this.

#### How to build GraphQL requests?

At the end, our query will look like this:

```graphql
query listContributions($after: String!) {
  rateLimit{
    cost
    remaining
  resetAt
  }
  search(query:"type:user", type:USER, first:20, after:$after){
    userCount
    edges{
      node{
      ... on User{
        id
        name
        repositoriesContributedTo(includeUserRepositories:true first:20 orderBy:{direction:DESC field:STARGAZERS}) {
          totalCount
          nodes{
            stargazers{
              totalCount
            }
            primaryLanguage{
            name
            }
            id
            name
          }
        }
      }
      }
      cursor
    }
  }
}
```
Don't worry, I will try to explain it step by step.

1. Declaring the request</li>
```graphql
query listContributions($after: String!) { ... }
```
Here we declare that we are considering a query, that we decide
to call "listContributions".
We also declare the String query argument "after" : we'll see later
how it is used.

1. Check rate limit

Now, fields that we wrap in the <code>{ ... }</code> part declared above will
directly apply to the "query" node. The <em>connections</em> and
<em>fields</em> available for the <code>query</code> object can be
found <a href="https://developer.github.com/v4/query/">there</a>.
We decide to fetch a field called "rateLimit" :<br/>
```graphql
rateLimit{
  cost
  remaining
  resetAt
}
```

I'm not going to detail each field there (but of course, you can
read the GitHub documentation if you want to know more about it) but
basically we will use this value to limit our requests, because the
final goal is to run those queries using a Python program, there
GitHub fixes a query rate limit, and we could have some troubles if
we tried to exceed it. =P

1. Fetching users

From there, <em>we could have</em> an entry point to directly list
all the nodes that correspond to GitHub <code>Users</code>. However,
this feature is still <a href="https://platform.github.community/t/how-to-list-up-all-users-in-github/3070">not implemented in the GitHub GraphQL API</a>
(at least in the public version).
So what we will do instead is a "search" (that is actually an other
field of the <code>query</code> object. With GraphQL,
<strong>everything</strong> is linked!)<br/>

```graphql
search(query:"type:user", type:USER, first:20, after:$after){ ... }
```

* `query:"type:user"` : to fetch all users, we set our search query as "type:user", what means "all the nodes with the type 'user'".
* `type:USER` : defines the type of our nodes. (could also be REPOSITORY, for example)
* `first:20` : number of user nodes returned by the
query. Can be up to 100, but actually the GitHub API often
returns server errors if this value is too high...
* `after:$after` : here is our query parameter! As
with the REST API, results are actually paginated, and so we can
iterate on results doing successive query passing each time the
last fetched `cursor` parameter to our query to
specify that we want nodes <em>after</em> the specified cursor
(we'll see how to get it later).


1. Handle Edges

```graphql
edges{
  node{
  ... on User{ ... }
  }
  cursor
}
```

The search results will be returned as `edges`, that
connect the `search` object to a list of `nodes`
that we consider as `Users`.
`cursor` corresponds to each node id : at each query we
keep the last one, and we use it to iterate over pages as explained
before.

1. Nodes data

And <strong>FINALLY</strong>, we reach to users and data that really
interest us!!
And because we previously declared `nodes` as `Users`,
we can call every connections and fields described in the <a href="https://developer.github.com/v4/object/user/">User documentation</a>.

```graphql
... on User{
  id
  name
  repositoriesContributedTo(includeUserRepositories:true first:20 orderBy:{direction:DESC field:STARGAZERS}) {
    totalCount
    nodes{
      stargazers{
        totalCount
      }
      primaryLanguage{
        name
      }
      id
      name
    }
  }
}
```

Notes :

* We only fetch the 20 first repositories by users, ordered by their number of stars, using the <code>repositoriesContributedTo</code>
described in the <a href="https://developer.github.com/v4/object/user/"> documentation </a></li>.

* Because it was actually quite easy from there, we also fetch
the `primaryLanguage` of each repository, because it could be a very interesting parameter to point out
clusters in our final graph.

1. Perform the request

Finally, our request needs to be embedded as a string in a JSON object
along with the variable values, that will be the body of the POST
request sent to https://api.github.com/graphql.
Here is, for example, how the body (set up in PostMan for example)
will look like:

```json
{
"query": "query listContributions ($after: String!) {rateLimit{cost remaining resetAt} search(query:\"type:user\", type:USER, first:2, after:$after){userCount pageInfo {endCursor} edges{node{... on User{id name repositoriesContributedTo(includeUserRepositories:true first:20 orderBy:{direction:DESC field:STARGAZERS}) {totalCount nodes{stargazers{totalCount} primaryLanguage{name}id name}}}}cursor}}}",
"variables":{"after": "Y3Vyc29yOjEw"}
}
```

As you can see that's quite ugly, but that's because the "query"
must be set up as a String, so you should not break lines... Also,
depending on what tool you use, do not forgot to escape quotes, and
be extra careful with spaces. ( if you want, you can directly
copy/paste the String above as the body of a POST request in PostMan to test it)

Also do not hesitate to use the <a href="https://developer.github.com/v4/explorer/">GitHub GraphQL explorer</a>
that will allow you to test your queries in a user-friendly way,
with syntax check!

Responses to the query above should look like that :

```json
 {
  "data": {
    "rateLimit": {
      "cost": 1,
      "remaining": 4989,
      "resetAt": "2018-12-13T18:24:10Z"
    },
    "search": {
      "userCount": 33720792,
      "pageInfo": {
        "endCursor": "Y3Vyc29yOjEy"
      },
      "edges": [
        {
          "node": {
            "id": "MDQ6VXNlcjI=",
            "name": "Chris Wanstrath",
            "repositoriesContributedTo": {
              "totalCount": 1,
              "nodes": [
                {
                "stargazers": {
                  "totalCount": 3199
                },
                "primaryLanguage": {
                  "name": "Ruby"
                },
                "id": "MDEwOlJlcG9zaXRvcnkxMzM2Nzc5",
                "name": "dotjs"
                }
              ]
            }
          },
          "cursor": "Y3Vyc29yOjEx"
        },
        {
          "node": {
            "id": "MDQ6VXNlcjg1NDc1Mzg=",
            "name": "Bucky Roberts",
            "repositoriesContributedTo": {
              "totalCount": 1,
              "nodes": [
                {
                "stargazers": {
                  "totalCount": 77
                },
                "primaryLanguage": {
                  "name": "Python"
                },
                "id": "MDEwOlJlcG9zaXRvcnk5MTE5ODcyOA==",
                "name": "Django-REST-Boilerplate"
                }
              ]
            }
          },
          "cursor": "Y3Vyc29yOjEy"
        }
      ]
    }
  }
 }
```

Normally you should see that all the fields that we specify in our
GraphQL query are there, and <strong>only those fields</strong>!

### Python implementation

All those steps, for the REST API as
for the GraphQL API, can be found in the Python package relative to this post. Feel free to use it or just
check the <a href="https://github.com/PaulBreugnot/GraphGitHub">GitHub repository</a>
if you need more information!


### Data fetching : results and conclusion.

Before ending this part about data fetching using the two GitHub APIs, I
would like to conclude on the pros and cons of those two, from my
personal experience.

REST API | GraphQL API
-------- | -----------
\+ Very simple to use. | \- Quite complex queries.
\- Lots of useless data. | \+ You get exactly what you want.
\+ You could theoretically fetch all GitHub data! | \- <strong>You can't fetch more than 1000 nodes in total, even with pagination!!</strong> Probably because of the same limitation on the REST <a href="https://developer.github.com/v3/search/#about-the-search-api">search API</a>.
\- <strong>HUGE</strong> amounts of requests needed in practice, so it's really hard to get a <em>huge</em> amount of data. | \- slow, and lots of problem from <a href="https://github.community/t5/GitHub-API-Development-and/Sporadic-502-errors-graphql-api/m-p/14434">GitHub server side</a>...


What is sure is that none of those APIs is supposed to be used to fetch
<em>all</em> GitHubs repository and users names, as I would have expected
before.

However, I was still able to use it to do quite an interesting analysis
plotting graphs using Gephi, and there could potentially be a lot of
applications...
But we'll see it in the [next part of this post](part2.md) !
