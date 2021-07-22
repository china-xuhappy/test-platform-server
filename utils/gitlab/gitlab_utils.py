
# client.auth()
from exts import gitlab_client

# project = gitlab_client.projects.get(2)
# print(project.http_url_to_repo)
# print(project.id)
# print(project.repository_tree(all=True))
# commits = project.commits.list()
# for c in commits:
#     print(dir(c))
#     print(c.author_name, c.message, c.title)
#     print(c.signature)
#     print(c.author_email)
#     print(c.diff)
    # print(c.statuses.list())


# Compare two branches, tags or commits:

def get_projects():
    projects = gitlab_client.projects.list(all=True)
    projects_list = []
    for project in projects:
        # print(dir(project))
        accessrequests = project.accessrequests
        additionalstatistics = project.additionalstatistics
        approvalrules = project.approvalrules
        approvals = project.approvals
        archive = project.archive
        artifact = project.artifact
        attributes = project.attributes
        avatar_url = project.avatar_url
        badges = project.badges
        boards = project.boards
        branches = project.branches
        clusters = project.clusters
        commits = project.commits
        create_fork_relation = project.create_fork_relation
        name = project.name
        id = project.id
        projects_list.append({
            "name": name,
            "id": id,
            # "accessrequests": accessrequests,
            # "additionalstatistics": additionalstatistics,
            # "approvalrules": approvalrules,
            # "approvals": approvals,
            # "archive": archive,
            # "artifact": artifact,
            # "attributes": attributes,
            # "avatar_url": avatar_url,
            # "badges": badges,
            # "boards": boards,
            # "branches": branches,
            # "clusters": clusters,
            # "commits": commits,
            # "create_fork_relation": create_fork_relation
        })

    return projects_list


def get_project_diffs(project_id,from_, to_):
    project = gitlab_client.projects.get(project_id)
    """
    获取两个分支 提交记录
    :return:
    """
    result = project.repository_compare(from_, to_)
    print("result: -> ",result)
    # # get the commits
    #
    # for commit in result['commits']:
    #     print(commit)
    #
    # get the diffs
    for file_diff in result['diffs']:
        print(str(file_diff).replace("'", "\""))

    return {
        "diffs": result['diffs'],
        "commits": result["commits"]
    }
