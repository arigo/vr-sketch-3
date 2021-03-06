﻿using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using BaroqueUI;


public class WorldScript : MonoBehaviour
{
    public enum Kind {
        Destroyed = 0,
        Polygon = 101,
        ColoredPolygon = 102,
        PolygonHighlight = 103,
        SelectedPolygon = 104,
        TextHint = 150,
        SmallSphere = 200,
        RectanglePointer = 201,
        CrossPointer = 202,
        MovePointer = 203,
        EraserPointer = 204,
        PencilPointer = 205,
        SelectPointer = 206,
        SelectPointerPlus = 207,
        SelectPointerMinus = 208,
        PushPullPointer = 209,
        Cylinder = 250,
        Stem = 251,
        DashedStem = 252,
        SelectedStem = 253,
    };


    /***************************************************************************************************/

    public GameObject distanceKeypadPrefab, referential, teleportEnabler;

    VRSketch3.PythonThread python_thread;

    List<WorldObject> world_objects;
    Dictionary<Kind, WorldObject> world_prefabs;
    List<Controller> active_controllers;
    GameObject current_dialog;

    GameObject frozen_by;
    int frozen_track_trigger;

    public void SetFrozenBy(GameObject freezing_dialog)
    {
        frozen_by = freezing_dialog;
        frozen_track_trigger = 1;   /* 2 = trigger released; 3 = trigger pressed again */
    }

    public GameObject IsCurrentlyFrozenBy()
    {
        return frozen_by;
    }

    public void UnFreeze()
    {
        if (frozen_by != null)
        {
            Destroy(frozen_by);
            frozen_by = null;
        }
    }

    public bool CheckController(Controller controller, int check_index)
    {
        return check_index >= 0 && check_index < active_controllers.Count &&
            controller == active_controllers[check_index];
    }

    public Controller ControllerByIndex(int index)
    {
        if (index < 0 || index >= active_controllers.Count)
            return null;
        return active_controllers[index];
    }

    public void ManualEnter(int token, float value)
    {
        if (token >= 0)
            python_thread.RequestManualEnter(token, value);
    }

    public void ApplyPendingUpdate(int index, int kind1, float[] data)
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
            wo.UpdateWorldObject(this, data);
    }

    private void Update()
    {
        /* every graphical frame update, fetch the next batch of pending
         * updates requested from Python and apply them to Unity */
        foreach (var pu_delegate in python_thread.NextUpdatesBatch())
            pu_delegate(this);
    }

    public void ShowMenu(int controller_num, string menu_string)
    {
        if (controller_num == 2000)    /* enable teleporter */
        {
            teleportEnabler.SetActive(true);
            return;
        }
        if (controller_num == 2001)    /* disable teleporter */
        {
            teleportEnabler.SetActive(false);
            return;
        }

        var menu = new Menu();
        foreach (var line in menu_string.Split('\n'))
        {
            int colon = line.IndexOf('\t');
            menu.Add(line.Substring(colon + 1), () => {
                python_thread.RequestClick(line.Substring(0, colon));
            });
        }
        GameObject requester = gameObject;
        if (controller_num >= 1000)
        {
            requester = null;
            controller_num -= 1000;
        }
        if (controller_num >= active_controllers.Count)
            return;   /* out of sync rare case, ignore */

        var dialog = menu.MakePopup(active_controllers[controller_num], requester);
        if (dialog == null)
            current_dialog = null;
        else
        {
            dialog.scrollWholeDialog = false;
            dialog.touchpadTouchAct = false;
            current_dialog = dialog.gameObject;
        }
    }

    private void Gt_onTouchPressDown(Controller controller)
    {
        if (current_dialog)
        {
            Destroy(current_dialog);
            current_dialog = null;
        }
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

        python_thread = new VRSketch3.PythonThread();

        var gt = Controller.GlobalTracker(this);
        gt.isConcurrent = true;
        gt.onControllersUpdate += Gt_onControllersUpdate;
        gt.onGripDown += Gt_onGripDown;
        gt.onGripDrag += Gt_onGripDrag;
        gt.onGripUp += Gt_onGripUp;
        gt.onTouchPressDown += Gt_onTouchPressDown;

        Gt_onControllersUpdate(new Controller[0]);
    }

    void UpdateActiveControllers(Controller[] controllers)
    {
        /* 'active_controllers = controllers' but trying to keep the order: even if a new
         * controller shows up before an existing one in the 'controllers' array, it will
         * be added after the existing entry in 'active_controllers'.
         */
        if (active_controllers == null)
            active_controllers = new List<Controller>();
        var ctrls = new HashSet<Controller>(controllers);
        int i = 0;
        while (i < active_controllers.Count)
            if (ctrls.Remove(active_controllers[i]))
                i++;
            else
                active_controllers.RemoveAt(i);
        active_controllers.AddRange(ctrls);
    }

    private void Gt_onControllersUpdate(Controller[] controllers)
    {
        if (frozen_by != null)
        {
            int pressed = 0;
            foreach (var ctrl in controllers)
                if (ctrl.triggerPressed)
                    pressed = 1;

            if ((frozen_track_trigger & 1) != pressed)
                frozen_track_trigger++;
            if (frozen_track_trigger < 4)
                return;

            UnFreeze();
        }

        UpdateActiveControllers(controllers);

        int j = active_controllers.Count * 4;
        if (current_dialog)
            j = 0;

        var data = new float[j + 5];
        data[j] = transform.localScale.y;
        data[j + 1] = Time.time;
        Vector3 head = transform.InverseTransformPoint(Baroque.GetHeadTransform().position);
        data[j + 2] = head.x;
        data[j + 3] = head.z;
        data[j + 4] = head.y;

        for (int o = 0; o < j; o += 4)
        {
            Controller ctrl = active_controllers[o / 4];
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
        python_thread.RequestFrame(j / 4, data);
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
        referential.SetActive(true);
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
        else
            referential.SetActive(false);
    }
}
