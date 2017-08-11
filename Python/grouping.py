from model import ModelStep, Group


def newgroup(app):
    for e in list(app.selected_edges):
        if e.group is not app.curgroup:
            app.selected_edges.discard(e)
    for g in list(app.selected_subgroups):
        if g.parent_group is not app.curgroup:
            app.selected_subgroups.discard(g)
    app.selection_updated(also_faces=True)

    count = len(app.selected_edges) + len(app.selected_subgroups)
    if count <= 1:
        return
    step = ModelStep(app.model, "New group")
    ng = Group(app.curgroup)
    
    # Create edges in the new group
    copies = {}
    for e in app.selected_edges:
        copies[e] = step.add_edge(ng, e.v1, e.v2)

    # Move faces to the new group
    remaining_edges = set()
    for face in app.model.get_faces(app.curgroup):
        if all(e in copies for e in face.edges):
            step.add_face([copies[e] for e in face.edges], paired_with=face)
            step.fe_remove.add(face)
        else:
            remaining_edges.update(face.edges)

    # Remove source edges unless they are part of other remaining faces
    for e in app.selected_edges:
        if e not in remaining_edges:
            step.fe_remove.add(e)

    # Move all selected groups
    #XXX missing

    app.execute_step(step)


def explodegroup(app):
    if len(app.selected_subgroups) != 1:
        return
    [subgroup] = app.selected_subgroups
    app.selected_subgroups.clear()
    app.selected_edges.clear()

    ng = app.curgroup
    step = ModelStep(app.model, "Explode group")

    # Move edges to the current group
    copies = {}
    for e in app.model.get_edges(subgroup):
        copies[e] = step.add_edge(ng, e.v1, e.v2)
        step.fe_remove.add(e)

    # Move faces to the current group
    for face in app.model.get_faces(subgroup):
        step.add_face([copies[e] for e in face.edges], paired_with=face)
        step.fe_remove.add(face)

    # Move sub-subgroups
    #XXX

    app.execute_step(step)

    app.selected_edges.update(copies.values())
    app.selection_updated(also_faces=True)
