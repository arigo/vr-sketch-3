using System.Collections;
using System.Collections.Generic;
using UnityEngine;


public class SphereObject : WorldObject
{
    public float localScale;
    static MaterialCache mcache;

    public override void UpdateWorldObject(WorldScript ws, float[] data)
    {
        transform.localPosition = GetVec3(data, 0);

        if (localScale > 0)
        {
            transform.localScale = Vector3.one * (localScale / transform.parent.lossyScale.y);
            if (data.Length > 3)
            {
                Controller ctrl = ws.ControllerByIndex((int)data[3]);
                if (ctrl != null)
                {
                    Vector3 fwd = ctrl.forward;
                    fwd.y = 0;
                    if (fwd.sqrMagnitude > 0.001f)
                        transform.rotation = Quaternion.LookRotation(fwd);
                }
            }
        }
        else
        {
            MeshRenderer rend = GetComponent<MeshRenderer>();
            if (rend != null)
            {
                if (mcache == null)
                    mcache = new MaterialCache(GetComponent<MeshRenderer>().sharedMaterial);

                Material mat;
                if (data.Length > 3)
                    mat = mcache.Get(GetColor24(data, 3));
                else
                    mat = mcache.Get();
                rend.sharedMaterial = mat;
            }
        }
    }
}
