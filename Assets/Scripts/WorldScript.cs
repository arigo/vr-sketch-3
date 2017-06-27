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
        RectanglePointer = 201,
        CrossPointer = 202,
        MovePointer = 203,
        Cylinder = 250,
        Stem = 251,
        DashedStem = 252,
    };

    public delegate void SignalErrorDelegate([In, MarshalAs(UnmanagedType.LPWStr)] string error);
    public delegate void UpdateDelegate(int index, int kind,
        [In, MarshalAs(UnmanagedType.LPArray, SizeParamIndex = 3)] float[] data, int data_count);
    public delegate void ApproxPlaneDelegate(
        [In, MarshalAs(UnmanagedType.LPArray, SizeParamIndex = 1)] float[] points, int coord_count,
        [Out, MarshalAs(UnmanagedType.LPArray, SizeConst = 4)] float[] plane);
    public delegate void ShowMenuDelegate(int controller_num,
        [In, MarshalAs(UnmanagedType.LPWStr)] string menu);

    [DllImport("PyUnityVR_cffi", CharSet = CharSet.Unicode)]
    public static extern int pyunityvr_init(SignalErrorDelegate error, UpdateDelegate update,
                                            ApproxPlaneDelegate approx_plane, ShowMenuDelegate show_menu);
    
    [DllImport("PyUnityVR_cffi")]
    public static extern int pyunityvr_frame(int num_ctrls, [In, MarshalAs(UnmanagedType.LPArray)] float[] controllers);

    [DllImport("PyUnityVR_cffi")]
    public static extern int pyunityvr_click([In, MarshalAs(UnmanagedType.LPWStr)] string id);


    /***************************************************************************************************/

    List<WorldObject> world_objects;
    Dictionary<Kind, WorldObject> world_prefabs;
    SignalErrorDelegate keepalive_error;
    UpdateDelegate keepalive_update;
    ApproxPlaneDelegate keepalive_approx_plane;
    ShowMenuDelegate keepalive_show_menu;
    Controller[] active_controllers;
    GameObject current_dialog;

    static void CB_SignalError(string error)
    {
        if (error.StartsWith("INFO:"))
        {
            Debug.Log(error.Substring(5));
        }
        else
        {
            Debug.LogError(error);
#if UNITY_EDITOR
            UnityEditor.EditorApplication.Beep();
#endif
        }
    }

    void CB_Update(int index, int kind1, float[] data, int data_count)
    {
        while (!(index < world_objects.Count))
            world_objects.Add(null);

        WorldObject wo = world_objects[index];
        Kind wo_kind = wo == null ? Kind.Destroyed : wo.kind;
        Kind kind = (Kind)kind1;

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

    void CB_ApproxPlane(float[] points, int coord_count, float[] plane)
    {
        Vector3[] pts = new Vector3[coord_count / 3];
        for (int i = 0; i < pts.Length; i++)
            pts[i] = new Vector3(points[3 * i],
                                 points[3 * i + 1],
                                 points[3 * i + 2]);
        Plane result = VRSketch3.PlaneRecomputer.RecomputePlane(pts);
        plane[0] = result.normal.x;
        plane[1] = result.normal.y;
        plane[2] = result.normal.z;
        plane[3] = result.distance;
    }

    void CB_ShowMenu(int controller_num, string menu_string)
    {
        var menu = new Menu();
        foreach (var line in menu_string.Split('\n'))
        {
            int colon = line.IndexOf(':');
            menu.Add(line.Substring(colon + 1), () => {
                if (pyunityvr_click(line.Substring(0, colon)) != 42)
                    Debug.LogError("pyunityvr_click() failed!");
            });
        }
        var dialog = menu.MakePopup(active_controllers[controller_num], gameObject);
        if (dialog == null)
            current_dialog = null;
        else
            current_dialog = dialog.gameObject;
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

        /* the delegate object themselves must remain alive for the duration of the whole run! */
        keepalive_error = CB_SignalError;
        keepalive_update = CB_Update;
        keepalive_approx_plane = CB_ApproxPlane;
        keepalive_show_menu = CB_ShowMenu;

        if (pyunityvr_init(keepalive_error, keepalive_update, keepalive_approx_plane, keepalive_show_menu) != 42)
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
        active_controllers = controllers;

        int j = controllers.Length * 4;
        if (current_dialog)
            j = 0;

        var data = new float[j + 2];
        data[j] = transform.localScale.y;
        data[j + 1] = Time.time;

        for (int o = 0; o < j; o += 4)
        {
            Controller ctrl = controllers[o / 4];
            int pressed = 0;
            if (ctrl.triggerPressed) pressed |= 1;
            if (ctrl.gripPressed) pressed |= 2;
            if (ctrl.touchpadPressed) pressed |= 4;

            Vector3 pos = transform.InverseTransformPoint(ctrl.position);
            data[o + 0] = pos.x;
            data[o + 1] = pos.z;
            data[o + 2] = pos.y;
            data[o + 3] = pressed;
        }
        if (pyunityvr_frame(j / 4, data) != 42)
            Debug.LogError("pyunityvr_frame() failed!");
    }


    /***************** Grip button *****************/

    Controller grip_first, grip_second;
    Quaternion grip_rotation;
    Vector3 grip_localcenter;
    float grip_scale;

    private void Gt_onGripDown(Controller controller)
    {
        Vector3 globalcenter;

        if (controller == grip_first || grip_first == null)
        {
            grip_first = controller;
            grip_second = null;
            globalcenter = controller.position;
        }
        else
        {
            grip_second = controller;

            Vector3 delta = grip_second.position - grip_first.position;
            grip_rotation = Quaternion.Inverse(Quaternion.LookRotation(new Vector3(delta.x, 0, delta.z)))
                * transform.rotation;
            grip_scale = transform.localScale.y / delta.magnitude;
            globalcenter = grip_first.position + delta * 0.5f;
        }
        grip_localcenter = transform.InverseTransformPoint(globalcenter);
    }

    private void Gt_onGripDrag(Controller controller)
    {
        if (controller != grip_first)
            return;

        Vector3 globalcenter_target;
        if (grip_second == null)
        {
            globalcenter_target = controller.position;
        }
        else
        {
            Vector3 delta = grip_second.position - grip_first.position;
            transform.rotation = Quaternion.LookRotation(new Vector3(delta.x, 0, delta.z)) * grip_rotation;

            transform.localScale = Vector3.one * (delta.magnitude * grip_scale);
            globalcenter_target = grip_first.position + delta * 0.5f;
        }
        Vector3 globalcenter_current = transform.TransformPoint(grip_localcenter);
        transform.position += globalcenter_target - globalcenter_current;
    }

    private void Gt_onGripUp(Controller controller)
    {
        if (controller == grip_first)
            grip_first = grip_second;
        grip_second = null;

        /* now grip_second == null && grip_first != controller */

        if (grip_first != null)
            Gt_onGripDown(grip_first);
    }
}