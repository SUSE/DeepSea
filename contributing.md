Contributor Guidelines
======================

Contributions to Deepsea are welcome and greatly appreciated, every little bit
helps in making the project a little better for everyone.

The following are a few guidelines to get you started contributing to DeepSea.

Signing your work
-----------------

In order to keep a record of code attributions, we expect you to sign-off your
patches. The rules are pretty simple and similar to many other open source
projects like the Linux kernel. If you can certify the below:

```
Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, is covered under an appropriate open source
    license and I have the right under that license to submit that
    work with modifications, whether created in whole or in part
    by me, under the same open source license (unless I am
    permitted to submit under a different license), as indicated
    in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```

then you just add a line saying

```
Signed-off-by: Random J Developer <random@developer.example.org>
```

using your real name (sorry, no pseudonyms or anonymous contributions.) in your
commit message.


Sending Patches
---------------

We accept patches via Github Pull Requests. Here is a quick guide to get you
going:

- [Fork the DeepSea repository](https://github.com/SUSE/DeepSea/fork), create a
  topic branch for the feature/fix. See the
  [Fork A Repo](https://help.github.com/articles/fork-a-repo/) documentation on
  github for more details. For a quick guide to git itself, [start
  here](http://rogerdudler.github.io/git-guide/).
- Avoid making changes directly to your master branch as it would make it harder
  to make changes or rebase later.
- Create logical changes into a single commit. Make multiple commits when it
  makes sense.
- We recommend commit titles to not exceed 50 characters and wrap the message
  itself to 80 characters.

  In summary:

  ```sh

  # hack, hack, hack
  $ git commit -s
  $ git push origin myfeature

  ```

- Submit a pull request at https://github.com/suse/deepsea/pulls and click on
  `New Pull Request`
- When addressing review comments, while you can add additional commits when it
  makes sense, preferably, you could also squash the changes onto relevant
  commits so as to have a nice clean history. The `git rebase -i` and `git
  squash` commands are your friends here. Once you've updated the local branch,
  you need to force push (if you've rebased) to the same branch with

  ```
  $ git push -f origin myfeature
  ```

-  Rebasing is also helpful when your change is based on an older parent commit
   which conflicts with the current master. In this case rebase will avoid the
   spurious merge commits.

Reporting Issues
----------------

Report issues/ request features via the github issues interface at
https://github.com/SUSE/DeepSea/issues/new
