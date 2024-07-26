"""
Some example code for working with the Caldera data set
"""
import json
import random

from pxr import Sdf, Usd, UsdGeom


def EditStage(edit_usd_file, source_usd_file ) -> Usd.Stage:
    """
    Edit the stage by adding the current file as a sublayer and set stage info.

    Args:
    ----
        edit_usd_file (str): A usd file we'll create to store the changes
        source_usd_file (str): The source USD file.

    Returns:
    -------
        Usd.Stage: The edited USD stage.

    """

    # create a new layer and open it
    layer = Sdf.Layer.CreateNew(edit_usd_file)
    stage = Usd.Stage.Open(layer)

    # add the existing file as a sublayer
    layer.subLayerPaths.append(source_usd_file)

    SetStageInfo(stage, "usd file created with the example script from the caldera data set.")

    return stage

def CountPrims(stage) -> dict:
    """
    Count the number of prims, meshes, verts, instances, and entities in the given stage. Note this
    just approximates the numbers, it's for illustrative purposes only.

    Args:
    ----
        stage (Usd.Stage): The USD stage to count the prims from.

    Returns:
    -------
        dict: A dictionary containing the count of prims, meshes, verts, instances, and entities.

    """

    info = {
        "prims": 0,
        "meshes": 0,
        "verts": 0,
        "prototypes": 0,
        "instances": 0,
        "entities": {},
    }

    # stage.Traverse by default wont walk into instances, so we add the flag
    for prim in stage.Traverse(Usd.TraverseInstanceProxies()):
        info["prims"] += 1

        if prim.IsA(UsdGeom.PointInstancer):
            # TODO: add the vert counts of the instnaced objects to the total points count
            info["prototypes"] += len(UsdGeom.PointInstancer(prim).GetProtoIndicesAttr().Get())
            info["instances"] += len(UsdGeom.PointInstancer(prim).GetPositionsAttr().Get())

        if prim.IsInstance():
            info["instances"] += 1

        if prim.IsA(UsdGeom.Mesh):
            info["meshes"] += 1
            info["verts"] += len(UsdGeom.Mesh(prim).GetPointsAttr().Get())

        elif prim.IsA(UsdGeom.Cube):
            atvi_classname = prim.GetCustomDataByKey("atvi:classname")
            if atvi_classname:
                
                if atvi_classname.startswith("scriptable_"):
                    atvi_classname = "scriptable"
            
                if atvi_classname in info["entities"]:
                    info["entities"][atvi_classname] += 1
                else:
                    info["entities"][atvi_classname] = 1
    return info


def SetPrimsEnabled(stage, prim_paths, active=True):
    """
    Set the enabled state of the prims in the given stage.

    Args:
    ----
        stage (Usd.Stage): The USD stage.
        prim_paths (list): A list of prim paths.
        active (bool, optional): The enabled state to set. Defaults to True.

    """
    for prim_path in prim_paths:
        prim = stage.GetPrimAtPath(prim_path)
        if prim:
            prim.SetActive(active)


def SetStageInfo(stage, comment="") -> None:
    """
    Set the stage info including the up axis, scale, time settings, and comment.

    Args:
    ----
        stage (Usd.Stage): The USD stage.
        comment (str, optional): The comment to set. Defaults to "".

    """

    # set the up axis to be z
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

    # set the scale to be inches
    UsdGeom.SetStageMetersPerUnit(stage, UsdGeom.LinearUnits.inches )

    # let's default to 30fps, as most animations do
    stage.SetFramesPerSecond(30)
    stage.SetTimeCodesPerSecond(30)
    
    # set the start and end time so we can scrub the timeline
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(900)

    # set the comment if provided
    if comment:
        stage.SetMetadata("comment", comment)

    filename = stage.GetRootLayer().realPath

    filename = filename.replace("\\", "/")


def SetVariantSets(stage, new_state):
    """
    Set the variant sets in the given stage to a new state.

    Args:
    ----
        stage (Usd.Stage): The USD stage.
        new_state (str): The new state to set for the variant sets.

    Returns:
    -------
        None

    """

    for prim in stage.Traverse():
        if prim.HasVariantSets():
            variant_sets = prim.GetVariantSets()
            for variant_name in  variant_sets.GetNames():
                variant_set = variant_sets.GetVariantSet(variant_name)

                options = variant_set.GetVariantNames()

                if "terrain" in variant_name or "district" in variant_name:

                    if new_state in options:
                        print(f"prim: {prim.GetPath()} has variant set {variant_name}")
                        before = variant_sets.GetVariantSelection(variant_name)
                        variant_set.SetVariantSelection(new_state)
                        after = variant_sets.GetVariantSelection(variant_name)
                        print(f"choices: {options} was: {before} now is: {after}")

def AddSublayer(stage, layer) -> None:
    """
    Add a sublayer to the given stage.

    Args:
    ----
        stage (Usd.Stage): The USD stage.
        layer (str): The path to the sublayer.

    Returns:
    -------
        None

    """

    # get the root layer of the stage
    root_layer = stage.GetRootLayer()

    # add the sublayer
    root_layer.subLayerPaths.append(layer)


def InspectPlayerPaths(stage) -> None:
    """
    Inspect player data in the given stage.

    Args:
    ----
        stage (Usd.Stage): The USD stage containing the player data.

    Returns:
    -------
        None

    """

    print(stage.GetRootLayer().realPath)
    # get the prim under which all the matches are kept
    root = stage.GetPrimAtPath("/players/breadcrumbs")

    # get all the matches
    matches = root.GetChildren()

    # pick a random one
    match = matches[random.randint(0, len(matches)-1)]
    print(f"looking at match {match.GetPath().name}")

    # same for the players
    players = match.GetChildren()
    # let's investigate this one
    player = players[random.randint(0, len(players)-1)]
    print(f"looking at player {player.GetPath().name}")

    # we stored the players as animated spheres, lets use
    # a more abstract class as we dont need sphere specific
    # properties right now
    locator = UsdGeom.Xformable(player)

    # to find the translation, let's inspect the transform ops
    translate_op = None
    for xform_op in locator.GetOrderedXformOps():
        if xform_op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            translate_op = xform_op
            break

    # lets see what samples we have for this locator
    time_samples = translate_op.GetTimeSamples()

    # time is sped up by 60, so 1 sec in the data is 1 min in the game
    time_scale = 60
    fps = stage.GetFramesPerSecond()

    # look up all the positions for the time samples we stored
    values = [ translate_op.Get(time=t) for t in time_samples]

    for i, time_sample in enumerate(time_samples):
        sample_time = time_scale*(time_sample/fps)
        print(f"at {sample_time:.2f} seconds, the position is {values[i]}")

def InspectEndpoints(stage):
    """
    Inspects the endpoints of players in a stage.

    Args:
    ----
        stage (Usd.Stage): The USD stage containing player endpoints.

    Returns:
    -------
        None

    Prints the longest duration a player lasted and the position at that time.
    """
    points_prim = UsdGeom.Points(stage.GetPrimAtPath("/players/endpoints/points_0"))
    positions = points_prim.GetPointsAttr().Get()
    
    # the times are stored in ms from the start of the match
    times = UsdGeom.PrimvarsAPI(points_prim).GetPrimvar("time").Get()

    max_time = 0
    position_at_max_time = None

    for i, time in enumerate(times):
        if time > max_time:
            max_time = time
            position_at_max_time = positions[i]
    
    print(f"the longest a player lasted was {max_time/1000.0:.2f} seconds, the position at that time was {position_at_max_time}")

if __name__ == "__main__":

    print("opening mp_wz_island")
    stage = EditStage("./caldera.usda", "./map_source/mp_wz_island.usd" )

    print("collecting statistics")
    print(json.dumps(CountPrims(stage), indent=4))

    print("setting the variants to proxy")
    SetVariantSets(stage, "proxy")

    print("adding the camera layer")
    AddSublayer(stage, "./layers/cameras.usd")

    print("adding player data")
    AddSublayer(stage, "./layers/breadcrumbs.usd")
    AddSublayer(stage, "./layers/endpoints.usd")

    print("saving the new stage")
    stage.GetRootLayer().Save()

    print("looking at the player paths")
    InspectPlayerPaths(Usd.Stage.Open("./layers/breadcrumbs.usd"))

    print("looking at the endpoints")
    InspectEndpoints(Usd.Stage.Open("./layers/endpoints.usd"))