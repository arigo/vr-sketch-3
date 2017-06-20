using System.Collections;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using UnityEngine;
using BaroqueUI;
using System;

public class WorldScript : MonoBehaviour
{
    public enum Kind {
        Destroyed = 0,
        Polygon = 101,
        ColoredPolygon = 102,
        PolygonHighlight = 103,
        SmallSphere = 200,
        Cylinder = 250,
    };

    public delegate void SignalErrorDelegate([In, MarshalAs(UnmanagedType.LPWStr)] string error);
    public delegate void UpdateDelegate(int index, int kind,
        [In, MarshalAs(UnmanagedType.LPArray, SizeParamIndex = 3)] float[] data, int data_count);

    [DllImport("PyUnityVR_cffi", CharSet = CharSet.Unicode)]
    public static extern int pyunityvr_init(SignalErrorDelegate error, UpdateDelegate update);
    
    [DllImport("PyUnityVR_cffi")]
    public static extern int pyunityvr_frame(int num_ctrls, [In, MarshalAs(UnmanagedType.LPArray)] float[] controllers);


    /***************************************************************************************************/

    List<WorldObject> world_objects;
    Dictionary<Kind, WorldObject> world_prefabs;
    static WorldScript world_script;

    static void CB_SignalError(string error)
    {
        Debug.LogError(error);
    }

    /* NB. a non-static callback seems to "half-work"... */
    static void CB_Update(int index, int kind, float[] data, int data_count)
    {
        world_script.UpdateWorldObject(index, (Kind)kind, data);
    }

    void UpdateWorldObject(int index, Kind kind, float[] data)
    {
        while (!(index < world_objects.Count))
            world_objects.Add(null);

        WorldObject wo = world_objects[index];
        Kind wo_kind = wo == null ? Kind.Destroyed : wo.kind;

        if (wo_kind != kind)
        {
            if (wo != null)
                DestroyImmediate(wo.gameObject);

            WorldObject prefab = world_prefabs[kind];
            if (prefab == null)
            {
                world_objects[index] = null;
                return;
            }

            wo = Instantiate(prefab, parent: transform);
            wo.name = prefab.name + " " + index;
            wo.kind = kind;
            world_objects[index] = wo;
        }

        if (wo != null)
            wo.UpdateWorldObject(data);
    }

    private void Start()
    {
        world_prefabs = new Dictionary<Kind, WorldObject>();
        foreach (var i in System.Enum.GetValues(typeof(Kind)))
        {
            Kind kind = (Kind)i;
            string s = "WorldObj/" + kind.ToString();
            WorldObject prefab = null;
            if (kind != Kind.Destroyed)
            {
                GameObject go = Resources.Load<GameObject>(s);
                if (go == null)
                {
                    Debug.LogError("Missing " + s);
                }
                else
                {
                    prefab = go.GetComponent<WorldObject>();
                    if (prefab == null)
                        Debug.LogError(s + " is missing a WorldObject script");
                }
            }
            world_prefabs[kind] = prefab;
        }

        world_objects = new List<WorldObject>();
        world_script = this;

        if (pyunityvr_init(CB_SignalError, CB_Update) != 42)
            Debug.LogError("pyunityvr_init() failed!");

        var gt = Controller.GlobalTracker(this);
        gt.isConcurrent = true;
        gt.onControllersUpdate += Gt_onControllersUpdate;
        gt.onGripDown += Gt_onGripDown;
        gt.onGripDrag += Gt_onGripDrag;
        gt.onGripUp += Gt_onGripUp;

        Gt_onControllersUpdate(new Controller[0]);
    }

    private void Gt_onControllersUpdate(Controller[] controllers)
    {
        var data = new float[controllers.Length * 4];

        for (int i = 0; i < controllers.Length; i++)
        {
            Controller ctrl = controllers[i];
            int o = 4 * i;
            int pressed = 0;
            if (ctrl.triggerPressed) pressed |= 1;
            if (ctrl.gripPressed) pressed |= 2;

            Vector3 pos = transform.InverseTransformPoint(ctrl.position);
            data[o + 0] = pos.x;
            data[o + 1] = pos.y;
            data[o + 2] = pos.z;
            data[o + 3] = pressed;
        }
        if (pyunityvr_frame(controllers.Length, data) != 42)
            Debug.LogError("pyunityvr_frame() failed!");
    }


    /***************** Grip button *****************/

    Vector3? grip_origin;
    Controller grip_first;
    Vector3? grip_delta;
    Quaternion grip_rotation;
    Vector3 grip_localcenter;
    float grip_scale;

    private void Gt_onGripDown(Controller controller)
    {
        if (grip_origin == null || controller == grip_first)
        {
            grip_first = controller;
            grip_origin = transform.position - controller.position;
            grip_delta = null;
        }
        else
        {
            Vector3 delta = controller.position - grip_first.position;
            grip_delta = delta;
            grip_rotation = Quaternion.Inverse(Quaternion.LookRotation(new Vector3(delta.x, 0, delta.z)))
                * transform.rotation;
            grip_scale = transform.localScale.y / delta.magnitude;
            Vector3 globalcenter = controller.position - delta * 0.5f;
            grip_localcenter = transform.InverseTransformPoint(globalcenter);
        }
    }

    private void Gt_onGripDrag(Controller controller)
    {
        if (grip_delta == null)
        {
            if (grip_origin == null)
                return;
            transform.position = grip_origin.Value + controller.position;
        }
        else if (controller != grip_first)
        {
            Vector3 delta = controller.position - grip_first.position;
            transform.rotation = Quaternion.LookRotation(new Vector3(delta.x, 0, delta.z)) * grip_rotation;

            transform.localScale = Vector3.one * (delta.magnitude * grip_scale);

            Vector3 globalcenter_target = controller.position - delta * 0.5f;
            Vector3 globalcenter_current = transform.TransformPoint(grip_localcenter);
            transform.position += globalcenter_target - globalcenter_current;
        }
    }

    private void Gt_onGripUp(Controller controller)
    {
        grip_delta = null;

        if (controller == grip_first || grip_first == null)
        {
            grip_first = null;
            grip_origin = null;
        }
        else
        {
            grip_origin = transform.position - grip_first.position;
        }
    }
}